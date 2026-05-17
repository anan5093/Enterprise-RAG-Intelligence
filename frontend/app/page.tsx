"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { getToken } from "@/lib/session";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // The old server redirect always hit /chat first, causing protected-page flashing.
    const destination = getToken() ? "/chat" : "/login";
    // replace() keeps transient auth routing out of browser history.
    router.replace(destination);
  }, [router]);

  return (
    <main className="grid min-h-screen place-items-center bg-ink px-6 text-paper">
      <div className="text-sm text-paper/60">Initializing secure session...</div>
    </main>
  );
}
