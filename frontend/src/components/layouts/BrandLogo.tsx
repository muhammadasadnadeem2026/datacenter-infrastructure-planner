/** HallPlan wordmark (text only). */
export function BrandLockup({ className = 'h-5' }: { className?: string }) {
  return (
    <svg viewBox="0 0 220 40" className={className} role="img" aria-label="HallPlan">
      <rect x="0" y="6" width="28" height="28" rx="6" fill="#F2A93B" />
      <path d="M8 26V14h4v4h4v-4h4v12h-4v-4h-4v4z" fill="#0A0A14" />
      <text x="38" y="30" fill="#FFFFFF" fontFamily="Inter, Arial, sans-serif" fontSize="24" fontWeight="700">HallPlan</text>
    </svg>
  );
}

export function BrandMonogram({ className = 'h-6' }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={className} role="img" aria-label="HallPlan">
      <rect x="6" y="6" width="28" height="28" rx="6" fill="#F2A93B" />
      <path d="M14 26V14h4v4h4v-4h4v12h-4v-4h-4v4z" fill="#0A0A14" />
    </svg>
  );
}
