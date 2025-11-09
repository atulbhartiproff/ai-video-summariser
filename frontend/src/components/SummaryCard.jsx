import React from 'react'

/**
 * SummaryCard component - Displays video summary in a clean card layout
 */
export default function SummaryCard({ summary, fileName, duration }) {
  // Parse summary text into key points (assuming bullet points or paragraphs)
  const parseSummary = (text) => {
    if (!text) return []
    
    // Split by newlines and filter empty lines
    const lines = text
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
    
    return lines
  }

  const keyPoints = parseSummary(summary)

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          Video Summary
        </h2>
        {fileName && (
          <p className="text-sm text-gray-500 mb-1">File: {fileName}</p>
        )}
        {duration && (
          <p className="text-sm text-gray-500">Duration: {duration}</p>
        )}
      </div>

      <div className="prose prose-sm max-w-none">
        {keyPoints.length > 0 ? (
          <ul className="space-y-3 list-none pl-0">
            {keyPoints.map((point, index) => (
              <li
                key={index}
                className="flex items-start gap-3 text-gray-700 leading-relaxed"
              >
                <span className="text-blue-500 mt-1.5">•</span>
                <span className="flex-1">{point}</span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-gray-600 whitespace-pre-wrap">{summary}</div>
        )}
      </div>
    </div>
  )
}

