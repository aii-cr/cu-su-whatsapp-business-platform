import { redirect } from 'next/navigation';

export default function Index() {
  // Redirect root to the login page
  redirect('/login');
}
