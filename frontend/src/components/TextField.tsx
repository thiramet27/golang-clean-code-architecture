import type { InputHTMLAttributes } from 'react'

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  name: string
}

export function TextField({ label, name, ...inputProps }: TextFieldProps) {
  return (
    <label className="field">
      <span>{label}</span>
      <input name={name} {...inputProps} />
    </label>
  )
}
