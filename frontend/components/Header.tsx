"use client";

import Link from "next/link";
import { ThemeToggle } from "./ThemeToggle";
import { Train } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl">
          <Train className="w-6 h-6 text-primary" />
          <span className="font-heading">Railway Reservation</span>
        </Link>
        
        <nav className="hidden md:flex items-center gap-6">
          <Link href="/" className="text-sm font-medium hover:text-primary transition-colors">
            Home
          </Link>
          <Link href="/search" className="text-sm font-medium hover:text-primary transition-colors">
            Search Trains
          </Link>
          <Link href="/bookings" className="text-sm font-medium hover:text-primary transition-colors">
            My Bookings
          </Link>
        </nav>
        
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Link 
            href="/login"
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            Login
          </Link>
        </div>
      </div>
    </header>
  );
}
