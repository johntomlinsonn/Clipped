import { Button } from "@/components/ui/button"
import { Check, ChevronDown } from "lucide-react"
import Link from "next/link"
import { SocialIcons } from "@/components/social-icons"
import { HowItWorks } from "@/components/how-it-works"
import { Footer } from "@/components/footer" // Import the new Footer component

export default function Component() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Navigation - Liquid Glass Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-white/30 backdrop-blur-lg rounded-b-3xl mx-4 mt-4 shadow-lg border border-white/50">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Check className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-semibold text-gray-900">Clipped</span>
        </div>

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

      {/* Main Content - Adjusted padding for fixed header */}
      <div className="pt-28 container mx-auto px-6 py-16">
        {" "}
        {/* Added pt-28 to push content down */}
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="space-y-8">
            <div className="inline-block bg-blue-50 text-blue-700 px-4 py-2 rounded-md text-sm">
              #1 AI Tool for Converting YouTube to Viral TikToks
            </div>

            <h1 className="text-5xl lg:text-6xl font-bold leading-tight">Turn any YouTube video into viral TikToks</h1>

            <p className="text-xl text-gray-600 leading-relaxed">
              AI-powered automation that transforms your YouTube content into engaging TikToks in seconds. Boost your
              social media presence and reach millions.
            </p>
            <div className="flex justify-start">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700 px-8 py-4 text-lg text-white">
                Try it now
              </Button>
            </div>

            <div className="flex flex-wrap gap-8 text-sm">
              <div className="flex items-center space-x-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>AI-powered editing</span>
              </div>
              <div className="flex items-center space-x-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Viral optimization</span>
              </div>
              <div className="flex items-center space-x-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Multi-platform posting</span>
              </div>
            </div>

            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-sm">G</span>
                </div>
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-sm">G2</span>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="w-4 h-4 bg-yellow-400 rounded-sm"></div>
                ))}
              </div>
              <span className="text-gray-400 text-sm">4.9 from 870 reviews</span>
            </div>
          </div>

          {/* Right Graphics */}
          <div className="relative h-[600px] hidden lg:block">
            {/* Floating Platform Icons */}
            <SocialIcons />

            {/* Purchase Notification Card */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 rotate-[-5deg]">
              <div className="bg-white/30 backdrop-blur-lg rounded-lg p-4 shadow-lg border border-white/50 w-64">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-10 h-10 bg-gray-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">AM</span>
                  </div>
                  <div>
                    <div className="text-gray-900 font-semibold text-sm">Alex M.</div>
                    <div className="text-gray-600 text-xs">12 sec ago</div>
                  </div>
                </div>
                <div className="inline-block bg-blue-600 text-white px-2 py-1 rounded text-xs font-semibold mb-2">
                  VIRAL POST
                </div>
                <div className="text-blue-400 font-bold text-lg">2.4M VIEWS</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <HowItWorks />

      {/* Footer */}
      <Footer />
    </div>
  )
}
