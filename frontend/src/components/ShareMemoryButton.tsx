import { useState } from "react";

import type { RelayMemory } from "../types/api";

interface Props {
  memory: RelayMemory;
}

export default function ShareMemoryButton({
  memory,
}: Props) {
  const [copied, setCopied] = useState(false);

  async function handleShare() {
    const text = `Relay Memory

Title:
${memory.title}

Summary:
${memory.summary}

Root Cause:
${memory.root_cause}

Resolution:
${memory.resolution}

Confidence:
${Math.round(memory.confidence * 100)}%

Memory Key:
${memory.memory_key}

Primary Asset:
${memory.primary_asset_urn}`;

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch {
      window.alert(
        "Unable to copy memory summary.",
      );
    }
  }

  return (
    <button
      className="relay-share-button"
      type="button"
      onClick={() => void handleShare()}
    >
      {copied
        ? "Copied"
        : "Copy share summary"}
    </button>
  );
}