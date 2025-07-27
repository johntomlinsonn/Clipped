"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Check, ChevronDown, Youtube, Download, Video, Scissors, Sparkles, CheckCircle } from "lucide-react"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"

export default function UploadPage() {
  const [videoUrl, setVideoUrl] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [clips, setClips] = useState<any[]>([])

  const processSteps = [
    { id: 1, title: "Downloading Video", icon: Download, description: "Fetching your YouTube video..." },
    { id: 2, title: "Analyzing Content", icon: Sparkles, description: "AI is identifying viral moments..." },
    { id: 3, title: "Creating Clips", icon: Scissors, description: "Generating optimized TikTok clips..." },
    { id: 4, title: "Complete", icon: CheckCircle, description: "Your viral clips are ready!" }
  ]

  const handleClipIt = async () => {
    if (!videoUrl) return
    setIsProcessing(true)
    setCurrentStep(0)
    setClips([])

    // Simulate processing steps visually
    for (let i = 0; i < processSteps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000))
      setCurrentStep(i + 1)
    }

    // Call backend API
    let videoId = videoUrl
    try {
      const res = await fetch("http://localhost:8000/full_flow/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: videoUrl })
      })
      if (!res.ok) throw new Error("Failed to process video")
      const data = await res.json()
      // POST the paths to /clips/ and receive video blobs
      const clipsRes = await fetch("http://localhost:8000/clips/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paths: data.clip_paths })
      })
      if (!clipsRes.ok) throw new Error("Failed to fetch clips")
      // Parse multipart response
      const boundary = clipsRes.headers.get('content-type')?.split('boundary=')[1]
      const buffer = await clipsRes.arrayBuffer()
      const decoder = new TextDecoder()
      const text = decoder.decode(buffer)
      // Split by boundary and filter out empty parts
      const parts = text.split(`--${boundary}`).filter(Boolean)
      const backendClips = parts.map((part, idx) => {
        // Find filename
        const filenameMatch = part.match(/filename="([^"]+)"/)
        const filename = filenameMatch ? filenameMatch[1] : `clip_${idx + 1}.mp4`
        // Find start of file data
        const fileStart = part.indexOf('\r\n\r\n') + 4
        const fileData = part.slice(fileStart)
        // Convert to blob
        const blob = new Blob([fileData], { type: 'video/mp4' })
        const url = URL.createObjectURL(blob)
        return {
          id: idx + 1,
          title: filename,
          duration: "--",
          views: "--",
          engagement: "--",
          thumbnail: url,
          videoUrl: url
        }
      })
      setClips(backendClips)
    } catch (err) {
      alert("Error processing video. Please try again.")
    }
    setIsProcessing(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Navigation - Liquid Glass Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-white/30 backdrop-blur-lg rounded-b-3xl mx-4 mt-4 shadow-lg border border-white/50">
        <Link href="/" className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Check className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-semibold text-gray-900">Clipped</span>
        </Link>

        <div className="hidden md:flex items-center space-x-8">
          <div className="flex items-center space-x-1 cursor-pointer text-gray-800 hover:text-blue-600 transition-colors">
            <span>Products</span>
            <ChevronDown className="w-4 h-4" />
          </div>
          <div className="flex items-center space-x-1 cursor-pointer text-gray-800 hover:text-blue-600 transition-colors">
            <span>Resources</span>
            <ChevronDown className="w-4 h-4" />
          </div>
          <Link href="#" className="text-gray-800 hover:text-blue-600 transition-colors">
            Integrations
          </Link>
          <Link href="#" className="text-gray-800 hover:text-blue-600 transition-colors">
            Pricing
          </Link>
        </div>

        <div className="flex items-center space-x-4">
          <Button variant="outline" className="border-gray-300 text-gray-700 hover:bg-gray-100 bg-transparent">
            Login
          </Button>
          <Button className="bg-blue-600 hover:bg-blue-700 text-white">Sign up</Button>
        </div>
      </nav>

      {/* Main Upload Section */}
      <div className="pt-32 pb-20">
        <div className="container mx-auto px-6 text-center">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Transform Your YouTube Video Into Viral TikToks
            </h1>
            <p className="text-xl text-gray-600 mb-12">
              Paste your YouTube link below and watch AI create engaging clips optimized for maximum reach.
            </p>

            {/* Upload Interface */}
            <div className="bg-white/30 backdrop-blur-lg rounded-xl shadow-2xl p-8 border border-white/50 mb-12">
              <div className="flex flex-col sm:flex-row gap-4 max-w-2xl mx-auto">
                <div className="flex-1 relative">
                  <Youtube className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <Input
                    type="url"
                    placeholder="Paste your YouTube video link here..."
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                    className="pl-12 p-4 text-lg border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <Button 
                  size="lg" 
                  onClick={handleClipIt}
                  disabled={!videoUrl || isProcessing}
                  className="bg-blue-600 hover:bg-blue-700 px-8 py-4 text-lg text-white disabled:opacity-50"
                >
                  {isProcessing ? "Processing..." : "Clip It!"}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Processing Flow Chart */}
        <AnimatePresence>
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -50 }}
              className="container mx-auto px-6 mb-20"
            >
              <div className="max-w-4xl mx-auto">
                <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
                  Processing Your Video
                </h2>
                
                <div className="relative">
                  {/* Progress Line */}
                  <div className="absolute top-12 left-0 right-0 h-1 bg-gray-200 rounded-full">
                    <motion.div
                      className="h-full bg-blue-500 rounded-full"
                      initial={{ width: "0%" }}
                      animate={{ 
                        width: currentStep === 0 ? "0%" : 
                               currentStep === 1 ? "33%" :
                               currentStep === 2 ? "66%" :
                               currentStep === 3 ? "100%" : "100%"
                      }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>

                  {/* Steps */}
                  <div className="grid grid-cols-4 gap-4">
                    {processSteps.map((step, index) => {
                      const isActive = currentStep === index + 1
                      const isCompleted = currentStep > index + 1
                      const IconComponent = step.icon

                      return (
                        <motion.div
                          key={step.id}
                          className="relative flex flex-col items-center text-center"
                          initial={{ scale: 0.8, opacity: 0.5 }}
                          animate={{ 
                            scale: isActive ? 1.1 : 1,
                            opacity: isActive || isCompleted ? 1 : 0.5
                          }}
                          transition={{ duration: 0.3 }}
                        >
                          {/* Step Icon */}
                          <div className={`
                            relative w-24 h-24 rounded-full flex items-center justify-center mb-4 border-4 transition-all duration-300
                            ${isActive ? 'border-blue-500 bg-blue-100 shadow-lg' : 
                              isCompleted ? 'border-green-500 bg-green-100' : 
                              'border-gray-300 bg-white'}
                          `}>
                            <IconComponent className={`
                              w-8 h-8 transition-colors duration-300
                              ${isActive ? 'text-blue-600' : 
                                isCompleted ? 'text-green-600' : 
                                'text-gray-400'}
                            `} />
                            
                            {/* Animated Pulse for Active Step */}
                            {isActive && (
                              <motion.div
                                className="absolute inset-0 rounded-full border-4 border-blue-400"
                                animate={{ scale: [1, 1.2, 1], opacity: [1, 0, 1] }}
                                transition={{ duration: 2, repeat: Infinity }}
                              />
                            )}
                          </div>

                          {/* Step Text */}
                          <h3 className="font-semibold text-gray-900 mb-1">{step.title}</h3>
                          <p className="text-sm text-gray-600">{step.description}</p>
                        </motion.div>
                      )
                    })}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Generated Clips Section */}
        <AnimatePresence>
          {clips.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              className="container mx-auto px-6"
            >
              <div className="max-w-6xl mx-auto">
                <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
                  Your Viral Clips Are Ready! 🎉
                </h2>
                <p className="text-xl text-center text-gray-600 mb-12">
                  AI has identified the most engaging moments and created optimized TikTok clips.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {clips.map((clip, index) => (
                    <motion.div
                      key={clip.id}
                      initial={{ opacity: 0, y: 50 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.2 }}
                      className="bg-white/30 backdrop-blur-lg rounded-xl shadow-lg border border-white/50 overflow-hidden hover:shadow-xl transition-shadow"
                    >
                      {/* Clip Thumbnail */}
                      <div className="relative h-64 bg-gray-200">
                        <video
                          src={clip.videoUrl}
                          controls
                          className="absolute inset-0 w-full h-full object-cover rounded-t-xl"
                        />
                        <div className="absolute bottom-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-sm">
                          {clip.duration}
                        </div>
                      </div>

                      {/* Clip Info */}
                      <div className="p-6">
                        <h3 className="font-bold text-lg text-gray-900 mb-3">{clip.title}</h3>
                        
                        <div className="flex justify-between text-sm mb-4">
                          <span className="text-gray-600">Predicted Views:</span>
                          <span className="font-semibold text-green-600">{clip.views}</span>
                        </div>
                        
                        <div className="flex justify-between text-sm mb-6">
                          <span className="text-gray-600">Engagement Rate:</span>
                          <span className="font-semibold text-blue-600">{clip.engagement}</span>
                        </div>

                        <div className="flex gap-2">
                          <a href={clip.videoUrl} download target="_blank" rel="noopener noreferrer" className="flex-1">
                            <Button className="w-full bg-blue-600 hover:bg-blue-700">
                              Download
                            </Button>
                          </a>
                          <Button variant="outline" className="flex-1" onClick={() => window.open(clip.videoUrl, '_blank')}>
                            Preview
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Action Buttons */}
                <div className="text-center mt-12">
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button size="lg" className="bg-green-600 hover:bg-green-700 px-8 py-4" onClick={() => {
                      clips.forEach(clip => {
                        const a = document.createElement('a');
                        a.href = clip.videoUrl;
                        a.download = `clip_${clip.id}.mp4`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                      });
                    }}>
                      Download All Clips
                    </Button>
                    <Button size="lg" variant="outline" className="px-8 py-4" onClick={() => window.location.reload()}>
                      Process Another Video
                    </Button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
