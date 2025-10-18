"use client";

import { File, X } from "lucide-react";
import type React from "react";

import { useState } from "react";

interface ApplicationFormProps {
  jobTitle: string;
}

export function ApplicationForm({ jobTitle }: ApplicationFormProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    coverLetter: "",
  });

  console.log(jobTitle);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("[v0] Form submitted:", { formData, files });
    alert("Application submitted successfully!");
  };

  return (
    <div className="rounded-lg border border-border bg-card p-8">
      <h2 className="mb-6 text-3xl font-bold text-card-foreground">
        Apply for this Position
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label
            htmlFor="name"
            className="mb-2 block text-sm font-medium text-card-foreground"
          >
            Full Name *
          </label>
          <input
            id="name"
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20"
            placeholder="John Doe"
          />
        </div>

        <div>
          <label
            htmlFor="email"
            className="mb-2 block text-sm font-medium text-card-foreground"
          >
            Email Address *
          </label>
          <input
            id="email"
            type="email"
            required
            value={formData.email}
            onChange={(e) =>
              setFormData({ ...formData, email: e.target.value })
            }
            className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20"
            placeholder="john@example.com"
          />
        </div>

        <div>
          <label
            htmlFor="phone"
            className="mb-2 block text-sm font-medium text-card-foreground"
          >
            Phone Number
          </label>
          <input
            id="phone"
            type="tel"
            value={formData.phone}
            onChange={(e) =>
              setFormData({ ...formData, phone: e.target.value })
            }
            className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20"
            placeholder="+1 (555) 000-0000"
          />
        </div>

        <div>
          <label
            htmlFor="coverLetter"
            className="mb-2 block text-sm font-medium text-card-foreground"
          >
            Cover Letter
          </label>
          <textarea
            id="coverLetter"
            rows={6}
            value={formData.coverLetter}
            onChange={(e) =>
              setFormData({ ...formData, coverLetter: e.target.value })
            }
            className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20"
            placeholder="Tell us why you're a great fit for this role..."
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-card-foreground">
            Resume / CV *
          </label>
          {/* <Dropzone
            onDrop={setFiles}
            maxSize={5 * 1024 ** 2}
            accept={[MIME_TYPES.pdf, MIME_TYPES.doc, MIME_TYPES.docx]}
            className="border-2 border-dashed border-input bg-background hover:bg-muted/50 transition-colors"
          >
            <div className="flex flex-col items-center justify-center gap-4 py-8">
              <Dropzone.Accept>
                <IconUpload size={50} className="text-primary" />
              </Dropzone.Accept>
              <Dropzone.Reject>
                <IconX size={50} className="text-destructive" />
              </Dropzone.Reject>
              <Dropzone.Idle>
                <IconUpload size={50} className="text-muted-foreground" />
              </Dropzone.Idle>

              <div className="text-center">
                <p className="text-lg font-medium text-card-foreground">
                  Drop your resume here or click to browse
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  PDF, DOC, or DOCX (max 5MB)
                </p>
              </div>
            </div>
          </Dropzone> */}

          {files.length > 0 && (
            <div className="mt-4 space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 rounded-lg border border-border bg-muted/50 p-3"
                >
                  <File size={20} className="text-primary" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-card-foreground">
                      {file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setFiles(files.filter((_, i) => i !== index))
                    }
                    className="text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <X size={20} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={files.length === 0}
          className="w-full rounded-lg bg-primary px-6 py-3 font-semibold text-primary-foreground transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
        >
          Submit Application
        </button>
      </form>
    </div>
  );
}
