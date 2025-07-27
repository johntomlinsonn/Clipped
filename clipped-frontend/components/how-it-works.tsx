"use client" // This component needs to be a client component for framer-motion

import { Youtube, ArrowRight, Sparkles, TrendingUp, Clock, Users, Zap, Share2, Wand } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import Image from "next/image"
import Link from "next/link"
import { motion } from "framer-motion" // Import motion from framer-motion

export function HowItWorks() {
  const cardVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
    hover: { scale: 1.05, boxShadow: "0px 10px 20px rgba(0, 0, 0, 0.1)" },
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  return (
    <section className="py-20 bg-gray-100">
      <div className="container mx-auto px-6 text-center">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">See Clipped in Action</h2>
        <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto">
          Witness the magic as your long-form content transforms into short, engaging, and viral-ready TikToks.
        </p>

        {/* Chrome Tab UI */}
        <div className="bg-white/30 backdrop-blur-lg rounded-xl shadow-2xl overflow-hidden border border-white/50 max-w-5xl mx-auto">
          {/* Tab Bar */}
          <div className="flex items-center bg-gray-100 px-4 py-2 border-b border-gray-200">
            <div className="flex space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>
            <div className="flex-1 mx-4 bg-white rounded-full px-4 py-1 text-sm text-gray-600 flex items-center justify-center border border-gray-300">
              <span className="mr-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="lucide lucide-lock"
                >
                  <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </span>
              clipped.ai/transform
            </div>
          </div>

          {/* Content Area */}
          <div className="p-8 flex flex-col items-center lg:flex-row lg:items-start justify-center gap-8">
            {/* YouTube Input */}
            <div className="flex flex-col items-center space-y-4">
              <h3 className="text-lg font-semibold text-gray-800">Your YouTube Video</h3>
              <div className="relative w-64 h-40 bg-gray-200 rounded-lg overflow-hidden shadow-md">
                <Image
                  src="/images/youtube-thumbnail.webp"
                  alt="YouTube Video Input"
                  layout="fill"
                  objectFit="cover"
                />
                <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                  <Youtube className="w-12 h-12 text-white" />
                </div>
              </div>
              <div className="mt-2 text-sm text-gray-700 font-medium">Every minute one person is eliminated</div>
              <div className="flex space-x-2 text-xs">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">1.2M views</span>
                <span className="px-2 py-1 bg-red-100 text-red-800 rounded">34K likes</span>
              </div>
              <p className="text-sm text-gray-500">Paste your link here</p>
            </div>

            {/* AI Layer */}
            <div className="flex flex-col items-center space-y-2 lg:space-y-0 lg:flex-row lg:space-x-4 lg:self-center">
              <ArrowRight className="w-8 h-8 text-blue-600 animate-pulse" />
              <div className="flex flex-col items-center text-center">
                <Sparkles className="w-10 h-10 text-purple-600" />
                <span className="text-sm font-medium text-gray-700 mt-1">AI Magic</span>
              </div>
              <ArrowRight className="w-8 h-8 text-blue-600 animate-pulse" />
            </div>

            {/* TikTok Outputs */}
            <div className="flex flex-col items-center space-y-4">
              <h3 className="text-lg font-semibold text-gray-800">Viral TikToks</h3>
              <div className="grid grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => {
                  // Define a single stat for each TikTok
                  const stats = [
                    { text: '1.5M views', bg: 'bg-red-100 text-red-800' },
                    { text: '80% retention', bg: 'bg-green-100 text-green-800' },
                    { text: '60% comment rate', bg: 'bg-blue-100 text-blue-800' },
                  ];
                  const stat = stats[i - 1];
                  return (
                    <div key={i} className="flex flex-col items-center">
                      <div className="relative w-24 h-40 rounded-lg overflow-hidden shadow-md">
                        <Image
                          src={`/images/tiktok-thumbnail-${i}.avif`}
                          alt={`TikTok Output ${i}`}
                          layout="fill"
                          objectFit="cover"
                        />
                      </div>
                      <div className={`mt-2 px-2 py-1 text-xs font-medium rounded ${stat.bg}`}>
                        {stat.text}
                      </div>
                    </div>
                  )
                })}
              </div>
              <p className="text-sm text-gray-500">Ready to go viral!</p>
            </div>
          </div>
        </div>

        {/* Input Area for YouTube Video */}
        <div className="mt-16 max-w-3xl mx-auto">
          <h2 className="text-4xl font-bold text-gray-900 mb-6">Create your first viral video now!</h2>
          <div className="flex flex-col sm:flex-row gap-4">
            <Input
              type="url"
              placeholder="Paste your YouTube video link here..."
              className="flex-1 p-3 text-lg border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
            <Link href="/upload">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700 px-8 py-4 text-lg text-white">
                Clip It!
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Why Clipped Section */}
      <div className="bg-gradient-to-br from-blue-50 to-purple-50 py-20 mt-20 relative overflow-hidden">
        {/* Background graphics */}
        <div className="absolute -top-10 -left-10 w-48 h-48 bg-blue-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob"></div>
        <div className="absolute -bottom-10 -right-10 w-64 h-64 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000"></div>

        <div className="container mx-auto px-6 text-center relative z-10">
          <h2 className="text-4xl font-bold text-blue-800 mb-12">Why Clipped? Unlock Your Viral Potential.</h2>
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10"
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            <motion.div
              className="bg-white/30 backdrop-blur-lg p-8 rounded-lg shadow-lg flex flex-col items-center text-center border border-white/50"
              variants={cardVariants}
              whileHover="hover"
            >
              <TrendingUp className="w-20 h-20 mb-4 text-blue-500" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Go Viral, Effortlessly</h3>
              <p className="text-gray-600">
                Our AI identifies the most engaging moments from your long videos, ensuring your TikToks are always
                optimized for maximum reach and virality.
              </p>
            </motion.div>
            <motion.div
              className="bg-white/30 backdrop-blur-lg p-8 rounded-lg shadow-lg flex flex-col items-center text-center border border-white/50"
              variants={cardVariants}
              whileHover="hover"
            >
              <Clock className="w-20 h-20 mb-4 text-green-500" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Save Hours, Not Minutes</h3>
              <p className="text-gray-600">
                Stop spending countless hours manually editing. Clipped automates the entire process, freeing up your
                time to create more content.
              </p>
            </motion.div>
            <motion.div
              className="bg-white/30 backdrop-blur-lg p-8 rounded-lg shadow-lg flex flex-col items-center text-center border border-white/50"
              variants={cardVariants}
              whileHover="hover"
            >
              <Users className="w-20 h-20 mb-4 text-red-500" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Boost Engagement & Growth</h3>
              <p className="text-gray-600">
                Consistently feed your audience fresh, high-quality short-form content across platforms, driving massive
                engagement and subscriber growth.
              </p>
            </motion.div>
            <motion.div
              className="bg-white/30 backdrop-blur-lg p-8 rounded-lg shadow-lg flex flex-col items-center text-center border border-white/50"
              variants={cardVariants}
              whileHover="hover"
            >
              <Zap className="w-20 h-20 mb-4 text-yellow-500" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Instant Content Creation</h3>
              <p className="text-gray-600">
                From YouTube link to viral TikToks in minutes. Clipped delivers ready-to-post videos, so you never miss
                a trend.
              </p>
            </motion.div>
            <motion.div
              className="bg-white/30 backdrop-blur-lg p-8 rounded-lg shadow-lg flex flex-col items-center text-center border border-white/50"
              variants={cardVariants}
              whileHover="hover"
            >
              <Share2 className="w-20 h-20 mb-4 text-purple-500" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Multi-Platform Ready</h3>
              <p className="text-gray-600">
                While optimized for TikTok, Clipped's outputs are perfect for YouTube Shorts, Instagram Reels, and more,
                maximizing your content's reach.
              </p>
            </motion.div>
            <motion.div
              className="bg-white/30 backdrop-blur-lg p-8 rounded-lg shadow-lg flex flex-col items-center text-center border border-white/50"
              variants={cardVariants}
              whileHover="hover"
            >
              <Wand className="w-20 h-20 mb-4 text-pink-500" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">AI-Powered Polish</h3>
              <p className="text-gray-600">
                Our AI doesn't just cut; it enhances. Expect dynamic captions, perfect timing, and a polished look that
                captivates viewers.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </div>
      {/* Tailwind CSS for blob animation */}
      <style jsx>{`
        @keyframes blob {
          0% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
          100% {
            transform: translate(0px, 0px) scale(1);
          }
        }
        .animate-blob {
          animation: blob 7s infinite cubic-bezier(0.6, 0.01, 0.3, 0.9);
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </section>
  )
}
