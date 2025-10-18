import { Briefcase } from "lucide-react";

export function Header() {
  return (
    <header className="rounded-t-none border border-t-0 rounded-md border-gray-300 bg-card">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <a href="/" className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Briefcase size={24} className="text-primary-foreground" />
            </div>
            <span className="text-xl font-semibold text-card-foreground">
              Careers
            </span>
          </a>

          <nav className="flex items-center gap-6">
            <a
              href="/"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Jobs
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
