"use client";

import Link from "next/link";

export function Footer() {
  return (
    <footer className="w-full border-t border-border bg-surface mt-auto">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-heading font-bold mb-4">Railway Reservation</h3>
            <p className="text-sm text-text-muted">
              Book train tickets easily with our comprehensive railway reservation system.
            </p>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/" className="text-text-muted hover:text-primary transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/search" className="text-text-muted hover:text-primary transition-colors">
                  Search Trains
                </Link>
              </li>
              <li>
                <Link href="/bookings" className="text-text-muted hover:text-primary transition-colors">
                  My Bookings
                </Link>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Support</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/help" className="text-text-muted hover:text-primary transition-colors">
                  Help Center
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-text-muted hover:text-primary transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link href="/faq" className="text-text-muted hover:text-primary transition-colors">
                  FAQ
                </Link>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/privacy" className="text-text-muted hover:text-primary transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-text-muted hover:text-primary transition-colors">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>
        
        <div className="mt-8 pt-8 border-t border-border text-center text-sm text-text-muted">
          <p>&copy; {new Date().getFullYear()} Railway Reservation System. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
