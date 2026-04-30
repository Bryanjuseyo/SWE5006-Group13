type LogoProps = {
  size?: 'sm' | 'lg';
};

export default function Logo({ size = 'sm' }: LogoProps) {
  const imgHeight = size === 'lg' ? 140 : 32;

  return (
    <div className="d-flex align-items-center">
      <img
        src="/logo.jpg"
        alt="CleanMatch"
        height={imgHeight}
        style={{ borderRadius: 12 }}
        className={size === 'lg' ? 'mb-3' : 'me-2'}
      />
      {size === 'sm' && (
        <span className="fw-bold text-primary fs-4">CleanMatch</span>
      )}
    </div>
  );
}
