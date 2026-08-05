import {
  useEffect,
  useState,
} from "react";

interface CopyButtonProps {
  value: string;
  idleLabel?: string;
  successLabel?: string;
  className?: string;
  disabled?: boolean;
}

type CopyState =
  | "idle"
  | "copying"
  | "copied"
  | "failed";

export default function CopyButton({
  value,
  idleLabel = "Copy",
  successLabel = "Copied",
  className = "",
  disabled = false,
}: CopyButtonProps) {
  const [copyState, setCopyState] =
    useState<CopyState>("idle");

  useEffect(() => {
    if (
      copyState !== "copied" &&
      copyState !== "failed"
    ) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setCopyState("idle");
    }, 2000);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [copyState]);

  async function handleCopy() {
    if (!value.trim() || disabled) {
      return;
    }

    setCopyState("copying");

    try {
      await navigator.clipboard.writeText(value);
      setCopyState("copied");
    } catch {
      try {
        const textArea =
          document.createElement("textarea");

        textArea.value = value;
        textArea.setAttribute(
          "readonly",
          "",
        );

        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        textArea.style.pointerEvents = "none";

        document.body.appendChild(textArea);
        textArea.select();

        const copied =
          document.execCommand("copy");

        document.body.removeChild(textArea);

        if (!copied) {
          throw new Error(
            "Clipboard copy failed.",
          );
        }

        setCopyState("copied");
      } catch {
        setCopyState("failed");
      }
    }
  }

  const label =
    copyState === "copying"
      ? "Copying…"
      : copyState === "copied"
        ? successLabel
        : copyState === "failed"
          ? "Copy failed"
          : idleLabel;

  return (
    <button
      className={[
        "relay-copy-button",
        copyState === "copied"
          ? "is-copied"
          : "",
        copyState === "failed"
          ? "is-failed"
          : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      type="button"
      disabled={
        disabled ||
        !value.trim() ||
        copyState === "copying"
      }
      onClick={() => void handleCopy()}
    >
      <span aria-hidden="true">
        {copyState === "copied"
          ? "✓"
          : "⧉"}
      </span>

      {label}
    </button>
  );
}