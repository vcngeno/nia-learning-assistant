import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Nia - AI Learning Assistant for K-12 Students',
  description: 'Safe, personalized AI tutoring platform for children. COPPA-compliant with full parental control.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
