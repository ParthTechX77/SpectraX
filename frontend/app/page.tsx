"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  Case,
  createCase,
  getCases,
} from "../lib/api/cases";

export default function Home() {
  const [cases, setCases] = useState<Case[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadCases() {
    try {
      setError(null);
      const data = await getCases();
      setCases(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load cases",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCases();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!title.trim()) {
      return;
    }

    try {
      setCreating(true);
      setError(null);

      await createCase({
        title: title.trim(),
        description: description.trim() || undefined,
      });

      setTitle("");
      setDescription("");

      await loadCases();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create case",
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-50 p-8 text-zinc-900">
      <div className="mx-auto max-w-4xl">
        <header>
          <h1 className="text-3xl font-bold">SpectraX</h1>
          <p className="mt-2 text-zinc-600">
            Multimodal AI forensics platform
          </p>
        </header>

        <section className="mt-8 rounded-xl border bg-white p-6">
          <h2 className="text-xl font-semibold">
            Create Case
          </h2>

          <form
            onSubmit={handleSubmit}
            className="mt-4 space-y-4"
          >
            <div>
              <label
                htmlFor="title"
                className="block text-sm font-medium"
              >
                Case title
              </label>

              <input
                id="title"
                value={title}
                onChange={(event) =>
                  setTitle(event.target.value)
                }
                className="mt-1 w-full rounded-lg border px-3 py-2"
                placeholder="Enter case title"
              />
            </div>

            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium"
              >
                Description
              </label>

              <textarea
                id="description"
                value={description}
                onChange={(event) =>
                  setDescription(event.target.value)
                }
                className="mt-1 w-full rounded-lg border px-3 py-2"
                rows={4}
                placeholder="Optional description"
              />
            </div>

            <button
              type="submit"
              disabled={creating || !title.trim()}
              className="rounded-lg bg-black px-5 py-2 text-white disabled:opacity-50"
            >
              {creating ? "Creating..." : "Create Case"}
            </button>
          </form>

          {error && (
            <p className="mt-4 rounded-lg bg-red-50 p-3 text-red-700">
              {error}
            </p>
          )}
        </section>

        <section className="mt-8 rounded-xl border bg-white p-6">
          <h2 className="text-xl font-semibold">
            Cases
          </h2>

          {loading && (
            <p className="mt-4 text-zinc-500">
              Loading cases...
            </p>
          )}

          {!loading && cases.length === 0 && (
            <p className="mt-4 text-zinc-500">
              No cases found.
            </p>
          )}

          <div className="mt-4 space-y-3">
            {cases.map((item) => (
              <div
                key={item.id}
                className="rounded-lg border p-4"
              >
                <div className="flex items-center justify-between gap-4">
                  <h3 className="font-semibold">
                    {item.title}
                  </h3>

                  <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs">
                    {item.status}
                  </span>
                </div>

                <p className="mt-1 text-sm text-zinc-500">
                  {item.case_number}
                </p>

                {item.description && (
                  <p className="mt-2 text-sm text-zinc-700">
                    {item.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}