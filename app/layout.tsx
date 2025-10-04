import './globals.css'
import 'leaflet/dist/leaflet.css'
import * as React from 'react'

export const metadata = {
  title: 'NASA TEMPO Air Quality Dashboard',
  description: 'North America Air Quality Monitoring: Precision from Orbit',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white">
        {children}
      </body>
    </html>
  );
}