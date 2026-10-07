import { useState } from 'react'

/**
 * A product photo that degrades gracefully. If the file is missing or fails to
 * load, it swaps to an inline Yale-blue placeholder instead of the browser's
 * broken-image icon — so a bad path never makes the storefront look broken.
 */
export function ProductImage({
  src,
  alt,
  className,
}: {
  src: string
  alt: string
  className?: string
}) {
  const [failed, setFailed] = useState(false)

  if (failed || !src) {
    return (
      <div className={className} role="img" aria-label={alt} data-placeholder="true">
        <svg viewBox="0 0 100 100" width="46" height="46" aria-hidden="true">
          <path
            d="M20 74 L40 48 L54 64 L68 44 L84 74 Z"
            fill="var(--yale-blue-light)"
            opacity="0.55"
          />
          <circle cx="36" cy="32" r="7" fill="var(--yale-blue-light)" opacity="0.55" />
        </svg>
      </div>
    )
  }

  return (
    <img
      className={className}
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  )
}
