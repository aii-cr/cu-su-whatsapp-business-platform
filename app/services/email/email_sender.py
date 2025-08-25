from __future__ import annotations

import mimetypes
import os
import smtplib
from email import encoders
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Dict, Iterable, List, Tuple, Union

from app.core.logger import logger


AttachmentSpec = Union[
    str,                            # path only
    Tuple[str, str],                # (filename, path)
    Dict[str, str],                 # {"filename": name, "file_path": path}
]


class EmailSender:
    def __init__(
        self,
        username: str,
        password: str,
        smtp_server: str,
        port: int,
        use_tls: bool = True,
        use_ssl: bool = False,
        custom_hostname: str | None = "mail.local",
    ) -> None:
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.custom_hostname = custom_hostname

    # ------------------------------------------------------------------ #
    #  PUBLIC METHODS                                                    #
    # ------------------------------------------------------------------ #
    def send_email(
        self,
        subject: str,
        body: str,
        to_addrs: Iterable[str],
        *,
        from_addr: str = "default",
        cc_addrs: Iterable[str] | None = None,
        bcc_addrs: Iterable[str] | None = None,
        attachments: Iterable[AttachmentSpec] | None = None,
    ) -> None:
        """Send plain-text email (with optional attachments)."""
        self._send(
            subject=subject,
            body_plain=body,
            body_html=None,
            to_addrs=to_addrs,
            from_addr=from_addr,
            cc_addrs=cc_addrs,
            bcc_addrs=bcc_addrs,
            attachments=attachments,
        )

    def send_html_email(
        self,
        subject: str,
        html_body: str,
        to_addrs: Iterable[str],
        *,
        from_addr: str = "default",
        cc_addrs: Iterable[str] | None = None,
        bcc_addrs: Iterable[str] | None = None,
        attachments: Iterable[AttachmentSpec] | None = None,
        high_priority: bool = False,
    ) -> None:
        """Send HTML email (with optional plain-text fallback + attachments)."""
        logger.info(f"📧 EmailSender.send_html_email called - subject: {subject}, to_addrs: {to_addrs}")
        self._send(
            subject=subject,
            body_plain=None,
            body_html=html_body,
            to_addrs=to_addrs,
            from_addr=from_addr,
            cc_addrs=cc_addrs,
            bcc_addrs=bcc_addrs,
            attachments=attachments,
            high_priority=high_priority,  
        )

    # ------------------------------------------------------------------ #
    #  INTERNAL CORE                                                     #
    # ------------------------------------------------------------------ #
    def _send(
        self,
        *,
        subject: str,
        body_plain: str | None,
        body_html: str | None,
        to_addrs: Iterable[str],
        from_addr: str,
        cc_addrs: Iterable[str] | None,
        bcc_addrs: Iterable[str] | None,
        attachments: Iterable[AttachmentSpec] | None,
        high_priority: bool = False, 
    ) -> None:
        try:
            from_addr = self.username if from_addr == "default" else from_addr
            to_addrs = self._to_list(to_addrs)
            cc_addrs = self._to_list(cc_addrs)
            bcc_addrs = self._to_list(bcc_addrs)
            attachments = self._to_list(attachments)

            # choose root container
            if body_html is not None:
                msg: MIMEMultipart | EmailMessage = MIMEMultipart("mixed")
                alt = MIMEMultipart("alternative")
                if body_plain:
                    alt.attach(MIMEText(body_plain, "plain", "utf-8"))
                alt.attach(MIMEText(body_html, "html", "utf-8"))
                msg.attach(alt)
            else:
                msg = EmailMessage()
                msg.set_content(body_plain or "", subtype="plain", charset="utf-8")

            msg["Subject"] = subject
            msg["From"] = formataddr((from_addr, self.username))
            if high_priority:
                msg["X-Priority"]  = "1"      
                msg["Priority"]    = "urgent"  # RFC-2156
                msg["Importance"]  = "high"    # MS Outlook
            msg["To"] = ", ".join(to_addrs)
            if cc_addrs:
                msg["Cc"] = ", ".join(cc_addrs)
            recipients = to_addrs + cc_addrs + bcc_addrs

            # attachments
            for spec in attachments:
                self._attach_file(msg, spec)

            self._connect_and_send(msg, from_addr, recipients)

        except Exception as e:
            logger.error("Failed to send email. Details: %s", e)
            raise

    # ------------------------------------------------------------------ #
    #  ATTACHMENT HANDLER                                                #
    # ------------------------------------------------------------------ #
    def _attach_file(
        self,
        msg: MIMEMultipart | EmailMessage,
        spec: AttachmentSpec,
    ) -> None:
        """
        Attach a file given by:
            • path str
            • (filename, path) tuple
            • {"filename": name, "file_path": path} dict
        """
        try:
            if isinstance(spec, tuple) and len(spec) == 2:
                filename, file_path = spec
            elif isinstance(spec, dict):
                filename = spec.get("filename") or os.path.basename(spec["file_path"])
                file_path = spec["file_path"]
            else:  # assume str path
                file_path = spec  # type: ignore
                filename = os.path.basename(file_path)

            mime_type, _ = mimetypes.guess_type(filename)
            main, sub = (mime_type or "application/octet-stream").split("/")

            with open(file_path, "rb") as fh:
                part = MIMEBase(main, sub)
                part.set_payload(fh.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(part)

        except Exception as e:
            logger.error("Failed to attach file %s. Details: %s", spec, e)
            raise

    # ------------------------------------------------------------------ #
    #  UTILS                                                             #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_list(value: Iterable | None) -> List:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    # ------------------------------------------------------------------ #
    #  SMTP SENDERS                                                      #
    # ------------------------------------------------------------------ #
    def _connect_and_send(
        self,
        msg: EmailMessage | MIMEMultipart,
        from_addr: str,
        recipients: List[str],
    ) -> None:
        logger.info(f"📧 Connecting to SMTP server: {self.smtp_server}:{self.port}")
        smtp_cls = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        with smtp_cls(self.smtp_server, self.port) as server:
            logger.info(f"📧 SMTP connection established")
            self._set_helo_and_send(server, msg, from_addr, recipients)

    def _set_helo_and_send(
        self,
        server: smtplib.SMTP,
        msg: EmailMessage | MIMEMultipart,
        from_addr: str,
        recipients: List[str],
    ) -> None:
        logger.info(f"📧 Starting SMTP handshake...")
        server.ehlo(self.custom_hostname or "")
        if self.use_tls:
            logger.info(f"📧 Starting TLS...")
            server.starttls()
            server.ehlo(self.custom_hostname or "")
        logger.info(f"📧 Logging in with username: {self.username}")
        server.login(self.username, self.password)
        logger.info(f"📧 Sending message to recipients: {recipients}")
        server.send_message(msg, from_addr=from_addr, to_addrs=recipients)
        logger.info(f"📧 Message sent successfully!")
