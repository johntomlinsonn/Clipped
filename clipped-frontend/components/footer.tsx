import Link from "next/link"
import { Check } from "lucide-react"

export function Footer() {
  return (
    <footer className="bg-gray-100 py-12 px-6 border-t border-gray-200">
      <div className="container mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Logo and Description */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Check className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-gray-900">Clipped</span>
          </div>
          <p className="text-gray-600 text-sm">
            AI-powered automation to transform your YouTube content into viral TikToks, effortlessly.
          </p>
        </div>

        {/* Products Links */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Products</h3>
          <ul className="space-y-2 text-gray-600 text-sm">
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                TikTok Creator
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                YouTube Shorts
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                Instagram Reels
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                AI Editing
              </Link>
            </li>
          </ul>
        </div>

        {/* Resources Links */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Resources</h3>
          <ul className="space-y-2 text-gray-600 text-sm">
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                Blog
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                Help Center
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                Tutorials
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                Case Studies
              </Link>
            </li>
          </ul>
        </div>

        {/* Company Links */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Company</h3>
          <ul className="space-y-2 text-gray-600 text-sm">
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                About Us
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                Careers
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                Contact
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-blue-600 transition-colors">
                Privacy Policy
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="container mx-auto mt-12 pt-8 border-t border-gray-200 text-center text-gray-500 text-sm">
        &copy; {new Date().getFullYear()} Clipped. All rights reserved.
      </div>
    </footer>
  )
}
