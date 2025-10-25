"use client";

import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { SearchForm } from "@/components/SearchForm";
import { motion } from "framer-motion";
import { Train, Clock, Shield, Users } from "lucide-react";

export default function Home() {
  const features = [
    {
      icon: Train,
      title: "8,990 Stations",
      description: "Access to entire railway network"
    },
    {
      icon: Clock,
      title: "Real-time Search",
      description: "Find trains in seconds"
    },
    {
      icon: Shield,
      title: "Secure Booking",
      description: "Safe and encrypted payments"
    },
    {
      icon: Users,
      title: "24/7 Support",
      description: "Always here to help you"
    }
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-gradient-to-br from-primary/10 via-secondary/5 to-accent/10 py-20">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center mb-12"
            >
              <h1 className="text-5xl md:text-6xl font-heading font-bold mb-4">
                Book Your Train Journey
              </h1>
              <p className="text-xl text-text-muted max-w-2xl mx-auto">
                Search from 5,208 trains across 8,990 stations. Fast, easy, and secure booking.
              </p>
            </motion.div>
            
            <SearchForm />
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16 bg-surface">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  whileHover={{ y: -5 }}
                  className="text-center p-6 rounded-xl bg-background border border-border hover:shadow-lg transition-shadow"
                >
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                    <feature.icon className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="text-xl font-heading font-bold mb-2">{feature.title}</h3>
                  <p className="text-text-muted">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-16">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
              >
                <div className="text-4xl md:text-5xl font-heading font-bold text-primary mb-2">
                  5,208
                </div>
                <div className="text-text-muted">Active Trains</div>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.1 }}
              >
                <div className="text-4xl md:text-5xl font-heading font-bold text-secondary mb-2">
                  8,990
                </div>
                <div className="text-text-muted">Railway Stations</div>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <div className="text-4xl md:text-5xl font-heading font-bold text-accent mb-2">
                  417K+
                </div>
                <div className="text-text-muted">Train Stops</div>
              </motion.div>
            </div>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  );
}

