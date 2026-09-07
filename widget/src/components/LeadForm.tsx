import { useState } from "react";
import type { FormEvent } from "react";

interface LeadFormProps {
  onSubmit: (fields: {
    full_name: string;
    email: string;
    contact_number: string;
  }) => Promise<{ success: boolean; errors?: Record<string, string> }>;
  disabled: boolean;
}

export function LeadForm({ onSubmit, disabled }: LeadFormProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [contactNumber, setContactNumber] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFieldErrors({});
    const result = await onSubmit({
      full_name: fullName,
      email,
      contact_number: contactNumber,
    });
    if (!result.success && result.errors) {
      setFieldErrors(result.errors);
    }
  };

  return (
    <form className="moin-chat-lead-form" onSubmit={handleSubmit}>
      <p className="moin-chat-lead-form__intro">
        To connect you with our team, could you share a few details?
      </p>

      <label className="moin-chat-lead-form__field">
        <span>Full name</span>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
          disabled={disabled}
          maxLength={200}
        />
        {fieldErrors.full_name && <span className="moin-chat-lead-form__error">{fieldErrors.full_name}</span>}
      </label>

      <label className="moin-chat-lead-form__field">
        <span>Email</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={disabled}
          maxLength={254}
        />
        {fieldErrors.email && <span className="moin-chat-lead-form__error">{fieldErrors.email}</span>}
      </label>

      <label className="moin-chat-lead-form__field">
        <span>Phone number</span>
        <input
          type="tel"
          value={contactNumber}
          onChange={(e) => setContactNumber(e.target.value)}
          required
          disabled={disabled}
          maxLength={32}
        />
        {fieldErrors.contact_number && (
          <span className="moin-chat-lead-form__error">{fieldErrors.contact_number}</span>
        )}
      </label>

      <button type="submit" className="moin-chat-lead-form__submit" disabled={disabled}>
        {disabled ? "Sending..." : "Submit"}
      </button>
    </form>
  );
}
