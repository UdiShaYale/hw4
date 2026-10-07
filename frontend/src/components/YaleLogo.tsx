/**
 * Yale shield, drawn inline so the app ships no binary assets.
 * The open book and the "Lux et Veritas" motto are the two features that make
 * the mark readable at a glance; `tone` flips it for dark (navy) backgrounds.
 */
export function YaleLogo({ size = 220, tone = 'light' }: { size?: number; tone?: 'light' | 'dark' }) {
  const shield = tone === 'light' ? '#ffffff' : 'var(--yale-blue)'
  const ink = tone === 'light' ? 'var(--yale-blue)' : '#ffffff'
  const page = tone === 'light' ? '#eef4fd' : '#ffffff'

  return (
    <svg
      width={size}
      height={size * 1.18}
      viewBox="0 0 200 236"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Yale University shield"
    >
      <path
        d="M10 10 h180 v126 c0 48 -44 74 -90 90 C54 210 10 184 10 136 Z"
        fill={shield}
        stroke={ink}
        strokeWidth="7"
        strokeLinejoin="round"
      />

      {/* Open book — two pages meeting at a spine. */}
      <path
        d="M34 62 C58 50 80 50 98 60 C116 50 138 50 162 62 L162 122 C138 110 116 110 98 120 C80 110 58 110 34 122 Z"
        fill={page}
        stroke={ink}
        strokeWidth="6"
        strokeLinejoin="round"
      />
      <path d="M98 60 L98 120" stroke={ink} strokeWidth="6" strokeLinecap="round" />

      {/* Hebrew on the pages, as on the real shield. */}
      <text x="66" y="97" textAnchor="middle" fill={ink} fontSize="16" fontWeight="700" fontFamily="Georgia, serif">
        אורים
      </text>
      <text x="130" y="97" textAnchor="middle" fill={ink} fontSize="16" fontWeight="700" fontFamily="Georgia, serif">
        ותמים
      </text>

      {/* Motto sits below the book, where the shield is still wide enough. */}
      <text x="100" y="162" textAnchor="middle" fill={ink} fontSize="26" fontWeight="700" letterSpacing="1.5" fontFamily="Georgia, serif">
        LUX ET
      </text>
      <text x="100" y="192" textAnchor="middle" fill={ink} fontSize="26" fontWeight="700" letterSpacing="1.5" fontFamily="Georgia, serif">
        VERITAS
      </text>
    </svg>
  )
}

/** Compact shield for the nav bar. */
export function YaleMark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size * 1.15} viewBox="0 0 200 236" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path
        d="M10 10 h180 v126 c0 48 -44 74 -90 90 C54 210 10 184 10 136 Z"
        fill="#ffffff"
        stroke="#ffffff"
        strokeWidth="7"
        strokeLinejoin="round"
      />
      <text
        x="100"
        y="160"
        textAnchor="middle"
        fill="var(--yale-blue)"
        fontSize="150"
        fontWeight="700"
        fontFamily="Georgia, serif"
      >
        Y
      </text>
    </svg>
  )
}
