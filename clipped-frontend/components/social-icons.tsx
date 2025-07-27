"use client" // This component needs to be a client component for framer-motion

import { motion } from "framer-motion"
import { SocialIcon } from "react-social-icons"

// Data for each orbiting icon with custom radii
const iconsData = [
	{
		url: "https://youtube.com",
		bgColor: "red-500",
		radius: 180, // Smallest orbit
		duration: 35, // Slightly faster
	},
	{
		url: "https://tiktok.com",
		bgColor: "black",
		radius: 320, // Largest orbit
		duration: 50, // Slower
	},
	{
		url: "https://linkedin.com",
		bgColor: "blue-700",
		radius: 230, // Medium orbit
		duration: 40,
	},
	{
		url: "https://reddit.com",
		bgColor: "orange-500",
		radius: 290, // Larger orbit
		duration: 45,
	},
	{
		url: "https://twitch.tv",
		bgColor: "purple-600",
		radius: 200, // Smaller orbit
		duration: 38,
	},
	{
		url: "https://github.com",
		bgColor: "gray-800",
		radius: 300, // Larger orbit
		duration: 48,
	},
	{
		url: "https://slack.com",
		bgColor: "green-600",
		radius: 250, // Medium orbit
		duration: 42,
	},
	{
		url: "https://instagram.com",
		bgColor: "pink-500",
		radius: 310, // Larger orbit
		duration: 49,
	},
	{
		url: "https://facebook.com",
		bgColor: "blue-800",
		radius: 220, // Medium orbit
		duration: 39,
	},
	{
		url: "https://twitter.com",
		bgColor: "black",
		radius: 190, // Smaller orbit
		duration: 36,
	},
	{
		url: "https://pinterest.com",
		bgColor: "red-700",
		radius: 285, // Larger orbit
		duration: 46,
	},
]

// Map tailwind bgColor keys to RGBA glow colors
const glowColors: Record<string, string> = {
	"red-500": "rgba(239,68,68,0.7)",
	black: "rgba(0,0,0,0.7)",
	"blue-700": "rgba(29,78,216,0.7)",
	"orange-500": "rgba(249,115,22,0.7)",
	"purple-600": "rgba(147,51,234,0.7)",
	"gray-800": "rgba(31,41,55,0.7)",
	"green-600": "rgba(22,163,74,0.7)",
	"pink-500": "rgba(236,72,153,0.7)",
	"blue-800": "rgba(30,64,175,0.7)",
	"red-700": "rgba(185,28,28,0.7)",
}

export function SocialIcons() {
	const containerSize = 64 // w-16 h-16 = 64px
	const numIcons = iconsData.length
	const angleStep = 360 / numIcons

	return (
		<div className="absolute inset-0 flex items-center justify-center">
			{/* Main orbiting container */}
			<motion.div
				className="relative w-full h-full flex items-center justify-center"
				// The main container still rotates, but individual icons will have their own speeds
				// This ensures the overall "system" rotates, but icons move independently
				animate={{ rotate: 360 }}
				transition={{
					duration: 120, // Slowed down rotation
					ease: "linear",
					repeat: Number.POSITIVE_INFINITY,
				}} // Continuous rotation for the overall system
			>
				{iconsData.map((data, index) => {
					const angle = index * angleStep
					// Calculate x and y positions on the circle using the custom radius
					const x = data.radius * Math.cos(angle * (Math.PI / 180))
					const y = data.radius * Math.sin(angle * (Math.PI / 180))
					// Vary size between 32 and 48px based on index
					const size = 32 + (index % 5) * 4
					// Determine glow shadow for some icons
					const glow =
						glowColors[data.bgColor] && index % 3 === 0
							? `0 0 8px ${glowColors[data.bgColor]}`
							: undefined

					return (
						<motion.div
							key={index}
							className={`absolute w-16 h-16 bg-${data.bgColor} rounded-full flex items-center justify-center`}
							style={{
								left: `calc(50% + ${x}px - ${containerSize / 2}px)`, // Center icon container horizontally
								top: `calc(50% + ${y}px - ${containerSize / 2}px)`, // Center icon container vertically
								boxShadow: glow, // Conditional colored glow
							}}
							// Each icon now has its own rotation speed and counter-rotation
							animate={{ rotate: -360 }} // Counter-rotate to keep the icon upright relative to the screen
							transition={{
								duration: data.duration,
								ease: "linear",
								repeat: Number.POSITIVE_INFINITY,
							}} // Use individual duration
							whileHover={{ scale: 1.2, transition: { duration: 0.2 } }} // Subtle hover effect
						>
							<motion.div
								animate={
									index % 2 === 0
										? { rotate: 360 }
										: {}
								}
								transition={
									index % 2 === 0
										? { duration: 4, ease: "linear", repeat: Infinity }
										: {}
								}
							>
								<SocialIcon
									url={data.url}
									fgColor="white"
									style={{ height: size, width: size }}
								/>
							</motion.div>
						</motion.div>
					)
				})}
			</motion.div>
		</div>
	)
}
