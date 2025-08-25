"""
Email templates for WhatsApp agent.
Contains HTML and text templates for confirmation emails.
"""

# Ultra-simple email template with inline styles for maximum compatibility
CONFIRMATION_EMAIL_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ADN Installation Confirmation</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f8f9fa;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px;">
        <!-- Header -->
        <div style="background-color: #1e3a8a; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <img src="https://imagenespaginadedatacr.s3.us-east-1.amazonaws.com/imagenes/logoADNazul2.png" 
                 alt="American Data Networks" 
                 style="width: 220px; height: auto; margin-bottom: 15px; border: 0;">
            <div style="color: white; font-size: 18px; font-weight: bold; margin-top: 10px;">Installation Confirmation</div>
        </div>
        <div style="height: 4px; background-color: #fbbf24; width: 100%;"></div>
        
        <!-- Content -->
        <div style="padding: 30px 25px;">
            <h1 style="font-size: 24px; font-weight: bold; color: #1e3a8a; margin-bottom: 15px;">Hi {full_name}! 👋</h1>
            
            <div style="display: inline-block; background-color: #10b981; color: white; padding: 8px 16px; border-radius: 15px; font-size: 14px; font-weight: bold; margin-bottom: 20px; text-transform: uppercase;">✅ Confirmed</div>
            
            <p style="font-size: 16px; color: #4b5563; margin-bottom: 20px; line-height: 1.6;">
                Your American Data Networks installation has been confirmed! We're excited to provide you with high-speed internet service.
            </p>
            
            <!-- Service Details -->
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 15px 0; border-top: 3px solid #3b82f6;">
                <h2 style="font-size: 16px; font-weight: bold; color: #1e3a8a; margin-bottom: 15px;">📡 Service Details</h2>
                <table style="width: 100%; border-collapse: collapse;" cellpadding="8" cellspacing="8">
                    <tr>
                        <td style="padding: 8px 12px; background: white; border: 1px solid #e5e7eb; border-radius: 6px; text-align: center;">
                            <div style="font-size: 12px; font-weight: bold; color: #6b7280; text-transform: uppercase; margin-bottom: 4px;">Plan</div>
                            <div style="font-size: 15px; font-weight: bold; color: #1f2937;">{plan_name}</div>
                        </td>
                        <td style="padding: 8px 12px; background: white; border: 1px solid #e5e7eb; border-radius: 6px; text-align: center;">
                            <div style="font-size: 12px; font-weight: bold; color: #6b7280; text-transform: uppercase; margin-bottom: 4px;">IPTV Devices</div>
                            <div style="font-size: 15px; font-weight: bold; color: #1f2937;">{iptv_count}</div>
                        </td>
                        <td style="padding: 8px 12px; background: white; border: 1px solid #e5e7eb; border-radius: 6px; text-align: center;">
                            <div style="font-size: 12px; font-weight: bold; color: #6b7280; text-transform: uppercase; margin-bottom: 4px;">VoIP Phone</div>
                            <div style="font-size: 15px; font-weight: bold; color: #1f2937;">{telefonia}</div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- Installation Details -->
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 15px 0; border-top: 3px solid #3b82f6;">
                <h2 style="font-size: 16px; font-weight: bold; color: #1e3a8a; margin-bottom: 15px;">📅 Installation Schedule</h2>
                <table style="width: 100%; border-collapse: collapse;" cellpadding="8" cellspacing="8">
                    <tr>
                        <td style="padding: 8px 12px; background: white; border: 1px solid #e5e7eb; border-radius: 6px; text-align: center;">
                            <div style="font-size: 12px; font-weight: bold; color: #6b7280; text-transform: uppercase; margin-bottom: 4px;">Date</div>
                            <div style="font-size: 15px; font-weight: bold; color: #1f2937;">{date}</div>
                        </td>
                        <td style="padding: 8px 12px; background: white; border: 1px solid #e5e7eb; border-radius: 6px; text-align: center;">
                            <div style="font-size: 12px; font-weight: bold; color: #6b7280; text-transform: uppercase; margin-bottom: 4px;">Time</div>
                            <div style="font-size: 15px; font-weight: bold; color: #1f2937;">{time_slot}</div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- Billing Information -->
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 15px 0; border-top: 3px solid #3b82f6;">
                <h2 style="font-size: 16px; font-weight: bold; color: #1e3a8a; margin-bottom: 15px;">💰 Billing Information</h2>
                <table style="width: 100%; border-collapse: collapse;" cellpadding="8" cellspacing="8">
                    <tr>
                        <td style="padding: 10px; background-color: #dcfce7; border: 1px solid #86efac; border-radius: 6px; text-align: center;">
                            <div style="font-size: 11px; font-weight: bold; color: #166534; text-transform: uppercase; margin-bottom: 4px;">Installation</div>
                            <div style="font-size: 14px; font-weight: bold; color: #15803d;">$0 FREE</div>
                        </td>
                        <td style="padding: 10px; background-color: #dcfce7; border: 1px solid #86efac; border-radius: 6px; text-align: center;">
                            <div style="font-size: 11px; font-weight: bold; color: #166534; text-transform: uppercase; margin-bottom: 4px;">First Month</div>
                            <div style="font-size: 14px; font-weight: bold; color: #15803d;">On Install Day</div>
                        </td>
                        <td style="padding: 10px; background-color: #dcfce7; border: 1px solid #86efac; border-radius: 6px; text-align: center;">
                            <div style="font-size: 11px; font-weight: bold; color: #166534; text-transform: uppercase; margin-bottom: 4px;">Second Month</div>
                            <div style="font-size: 14px; font-weight: bold; color: #15803d;">FREE</div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- Confirmation Number -->
            <div style="background-color: #1e3a8a; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <h2 style="font-size: 16px; font-weight: bold; margin-bottom: 10px;">🎫 Your Confirmation Number</h2>
                <div style="font-size: 20px; font-weight: bold; letter-spacing: 1px; margin: 10px 0; padding: 10px 15px; background-color: rgba(255, 255, 255, 0.2); border-radius: 6px; display: inline-block;">{confirmation_number}</div>
                <p style="font-size: 14px; margin-top: 8px;">Please save this number for your records</p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #f1f5f9; border-radius: 6px;">
                <p style="color: #475569; font-size: 14px; margin-bottom: 10px;">
                    Need help or have questions? We're here for you! 💬
                </p>
                <p style="color: #1e3a8a; font-weight: bold; font-size: 16px;">
                    Thank you for choosing American Data Networks! 🚀
                </p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #1f2937; color: #9ca3af; padding: 20px; text-align: center; border-radius: 0 0 8px 8px;">
            <p style="font-size: 15px; font-weight: bold; margin-bottom: 8px; color: #d1d5db;">
                🌐 American Data Networks - Costa Rica
            </p>
            <p style="font-size: 13px; color: #9ca3af;">
                📧 <a href="mailto:support@adn.cr" style="color: #60a5fa; text-decoration: none;">support@adn.cr</a> | 
                📞 <a href="tel:+50640004236" style="color: #60a5fa; text-decoration: none;">+506 4000-ADN</a> | 
                🔗 <a href="https://www.adn.cr" style="color: #60a5fa; text-decoration: none;">www.adn.cr</a>
            </p>
        </div>
    </div>
</body>
</html>"""

# Fallback text template for email clients that don't support HTML
CONFIRMATION_EMAIL_TEXT = """Hi {full_name},

Your American Data Networks installation is confirmed.

Service:
- Plan: {plan_name}
- IPTV devices: {iptv_count}
- VoIP Phone: {telefonia}

Installation:
- Date: {date}
- Time: {time_slot}

Billing:
- First month pre-charge on installation day.
- Installation cost: $0
- Second month: FREE

Confirmation Number: {confirmation_number}

If you need any changes, just reply to this message.
Thanks for choosing American Data Networks!"""
