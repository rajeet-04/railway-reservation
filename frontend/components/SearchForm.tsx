"use client";

import { useState } from "react";
import { Search, Calendar, MapPin } from "lucide-react";
import { motion } from "framer-motion";

export function SearchForm() {
  const [fromStation, setFromStation] = useState("");
  const [toStation, setToStation] = useState("");
  const [date, setDate] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle search
    console.log("Search:", { fromStation, toStation, date });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-4xl mx-auto"
    >
      <form onSubmit={handleSubmit} className="bg-surface rounded-2xl shadow-xl p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <label htmlFor="from" className="block text-sm font-medium">
              <MapPin className="inline w-4 h-4 mr-2" />
              From Station
            </label>
            <input
              id="from"
              type="text"
              value={fromStation}
              onChange={(e) => setFromStation(e.target.value)}
              placeholder="e.g., New Delhi"
              className="w-full px-4 py-3 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="to" className="block text-sm font-medium">
              <MapPin className="inline w-4 h-4 mr-2" />
              To Station
            </label>
            <input
              id="to"
              type="text"
              value={toStation}
              onChange={(e) => setToStation(e.target.value)}
              placeholder="e.g., Mumbai"
              className="w-full px-4 py-3 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="date" className="block text-sm font-medium">
              <Calendar className="inline w-4 h-4 mr-2" />
              Journey Date
            </label>
            <input
              id="date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>
        </div>

        <motion.button
          type="submit"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="mt-6 w-full bg-primary text-white py-4 rounded-lg font-semibold hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
        >
          <Search className="w-5 h-5" />
          Search Trains
        </motion.button>
      </form>
    </motion.div>
  );
}
