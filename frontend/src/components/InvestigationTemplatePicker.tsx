import type {
  InvestigationCreateInput,
} from "../types/api";

interface InvestigationTemplatePickerProps {
  onSelect: (
    template: InvestigationCreateInput,
  ) => void;
}

interface InvestigationTemplate {
  id: string;
  label: string;
  description: string;
  input: InvestigationCreateInput;
}

const INVESTIGATION_TEMPLATES: InvestigationTemplate[] = [
  {
    id: "revenue-schema-change",
    label: "Revenue dashboard drop",
    description:
      "Investigate a revenue reporting failure caused by an upstream customer_id schema change.",
    input: {
      title:
        "Revenue dashboard dropped after customer_id schema update",
      description:
        "Revenue totals fell after the upstream customer_id field changed type. Investigate the affected joins, downstream models, and dashboard impact.",
      asset_urn:
        "urn:li:dashboard:(looker,revenue_dashboard)",
      priority: "high",
    },
  },
];

export default function InvestigationTemplatePicker({
  onSelect,
}: InvestigationTemplatePickerProps) {
  return (
    <section className="relay-template-picker">
      <header>
        <div>
          <p className="relay-eyebrow">
            Quick-start scenario
          </p>

          <h3>Start from a known incident pattern</h3>
        </div>

        <span>Optional</span>
      </header>

      <div className="relay-template-grid">
        {INVESTIGATION_TEMPLATES.map((template) => (
          <button
            key={template.id}
            className="relay-template-card"
            type="button"
            onClick={() =>
              onSelect({
                ...template.input,
              })
            }
          >
            <strong>{template.label}</strong>

            <p>{template.description}</p>

            <span>Use template →</span>
          </button>
        ))}
      </div>
    </section>
  );
}