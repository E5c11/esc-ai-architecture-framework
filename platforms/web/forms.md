---
id: PLAT-WEB-FORMS
type: guide
layer: platforms
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP-ERR-CLASSES]
related: [PLAT-WEB-HTTP]
tags: [forms, react-hook-form, zod, validation, ssot, field-errors, discriminated-union]
---

# Forms — `react-hook-form` + `zod`

## Motivating case

A content-authoring surface that edits a discriminated content type — one
zod schema per question `presentation` type (`fitb`, `fraction`,
`multiple_choice`, ...), each with genuinely different fields — is the
concrete case this doc was written from. The rules below are stated
generally: they apply to any form backed by a discriminated content type,
not just questions.

## One schema per variant

```rule
id: PLAT-WEB-FORMS-SCHEMA-01
statement: A form backed by a discriminated content type (a `presentation`/`type`/`kind` field selecting the shape) MUST define one zod schema per variant — never one generic schema covering the superset of every variant's fields.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-FORMS-SCHEMA-01 — define one zod schema per content variant; a generic superset schema validates nothing type-specific.
```

```typescript
// ❌ Wrong — every field is optional, so nothing is actually validated
const questionSchema = z.object({
  presentation: z.enum(['fitb', 'fraction', 'multiple_choice']),
  tokens: z.array(z.string()).optional(),      // fitb-only
  numerator: z.number().optional(),             // fraction-only
  options: z.array(z.string()).optional(),      // multiple_choice-only
});

// ✅ Correct — each variant's schema requires exactly its own fields
const fitbSchema = z.object({
  presentation: z.literal('fitb'),
  tokens: z.array(z.string()).min(1),
});
const fractionSchema = z.object({
  presentation: z.literal('fraction'),
  numerator: z.number().int(),
  denominator: z.number().int().positive(),
});
const multipleChoiceSchema = z.object({
  presentation: z.literal('multiple_choice'),
  options: z.array(z.string()).min(2),
  correctIndex: z.number().int().nonnegative(),
});

const questionSchema = z.discriminatedUnion('presentation', [
  fitbSchema,
  fractionSchema,
  multipleChoiceSchema,
]);
```

`z.discriminatedUnion` is what makes the superset schema unnecessary — zod
picks the right branch off the `presentation` field and validates only that
branch's fields, so nothing type-specific is ever silently skipped.

## Client/server schema reuse

```rule
id: PLAT-WEB-FORMS-SSOT-01
statement: The zod schema used for client-side react-hook-form validation MUST be reused, not re-derived, for server-side validation inside the Server Action that receives the submission.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-FORMS-SSOT-01 — never validate only on the client; reuse the same schema server-side (CORE-SSOT applied to validation).
```

```typescript
// features/questions/schema.ts — imported by both the form and the action
export const fitbSchema = z.object({ /* ... */ });

// features/questions/components/FitbForm.tsx
const form = useForm({ resolver: zodResolver(fitbSchema) });

// features/questions/actions/createFitbQuestion.ts
'use server';
export async function createFitbQuestion(input: unknown): Promise<Outcome<Question>> {
  const parsed = fitbSchema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: { type: 'validation', fieldErrors: parsed.error.flatten().fieldErrors } };
  }
  // ...
}
```

A Server Action is reachable directly (not only through the form that
happens to render it) — client-only validation is not validation at all
from the server's perspective. Re-deriving an equivalent-but-separate
server schema is the specific failure this rule targets: two schemas drift
the moment one changes and the other doesn't.

## Error mapping

```rule
id: PLAT-WEB-FORMS-ERR-01
statement: A `validation` `AppError` returned from a Server Action MUST be mapped into react-hook-form's `setError` via its `fieldErrors`, not surfaced as a single generic error message.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-FORMS-ERR-01 — cites ARCH-WEB-APP-ERR-CLASSES's `fieldErrors` shape, which exists specifically so this mapping needs no adapter.
```

```typescript
const result = await createFitbQuestion(values);
if (!result.ok && result.error.type === 'validation') {
  for (const [field, messages] of Object.entries(result.error.fieldErrors)) {
    form.setError(field as keyof FitbFormValues, { message: messages[0] });
  }
  return;
}
```

`ARCH-WEB-APP-ERR-CLASSES`'s `validation` error is shaped exactly like
zod's `.flatten().fieldErrors` for this reason — the mapping above is a
direct pass-through, not a translation layer that has to reshape one error
format into another.

## `zodResolver` wiring and field arrays

Worked examples, not new rules — the shape varies too much per content type
to standardize further than "one schema per variant."

```typescript
const form = useForm<z.infer<typeof fitbSchema>>({
  resolver: zodResolver(fitbSchema),
  defaultValues: { presentation: 'fitb', tokens: [''] },
});
```

A blank-token-list editor for a `fitb`-shaped schema uses `useFieldArray`
to let the author add/remove tokens without hand-rolling array state:

```typescript
const { fields, append, remove } = useFieldArray({ control: form.control, name: 'tokens' });

return (
  <>
    {fields.map((field, index) => (
      <div key={field.id}>
        <input {...form.register(`tokens.${index}`)} />
        <button type="button" onClick={() => remove(index)}>Remove</button>
      </div>
    ))}
    <button type="button" onClick={() => append('')}>Add token</button>
  </>
);
```

A `multiple_choice` variant's field array (an `options` list plus a
`correctIndex` selector) follows the same `useFieldArray` shape with
different per-item fields — the pattern generalizes, only the fields
change per `presentation`.
