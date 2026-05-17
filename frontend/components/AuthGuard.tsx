"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken } from "@/lib/session";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      // Auth depends on localStorage, so protected UI must wait until the client check completes.
      router.replace("/login");
      return;
    }
    setAuthorized(true);
  }, [router]);

  if (!authorized) {
    return (
      <main className="grid min-h-screen place-items-center bg-ink px-6 text-paper">
        <div className="text-sm text-paper/60">Checking secure session...</div>
      </main>
    );
  }

  return <>{children}</>;
}
