import { useEffect, useMemo, useState } from 'react'
import { paymentsApi, studentsApi, invoicesApi, Student, Invoice } from '../api/client'

type PaymentLine = {
  invoice_id: string
  amount_cents: string
}

const PAYMENT_METHODS = [
  { value: 'cash', label: 'Cash' },
  { value: 'credit_card', label: 'Credit Card' },
  { value: 'debit_card', label: 'Debit Card' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'wire_transfer', label: 'Wire Transfer' },
  { value: 'check', label: 'Check' },
  { value: 'other', label: 'Other' },
]

export default function Payments() {
  const [students, setStudents] = useState<Student[]>([])
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)

  const [studentId, setStudentId] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('')
  const [currency, setCurrency] = useState('USD')
  const [lines, setLines] = useState<PaymentLine[]>([{ invoice_id: '', amount_cents: '' }])

  useEffect(() => {
    loadStudents()
  }, [])

  useEffect(() => {
    if (!studentId) {
      setInvoices([])
      return
    }
    loadInvoices(studentId)
  }, [studentId])

  const loadStudents = async () => {
    try {
      const res = await studentsApi.list()
      setStudents(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadInvoices = async (sid: string) => {
    try {
      const res = await invoicesApi.list(sid)
      setInvoices(res.data)
      const firstCurrency = res.data[0]?.currency
      if (firstCurrency) {
        setCurrency(firstCurrency)
      }
    } catch (e) {
      console.error(e)
    }
  }

  const totalCents = useMemo(() => {
    return lines.reduce((acc, line) => {
      const v = parseInt(line.amount_cents || '0', 10)
      return acc + (Number.isFinite(v) ? v : 0)
    }, 0)
  }, [lines])

  const formatMoney = (cents: number, cur: string) => `${cur} ${(cents / 100).toFixed(2)}`

  const addLine = () => setLines((prev) => [...prev, { invoice_id: '', amount_cents: '' }])

  const removeLine = (idx: number) => {
    setLines((prev) => prev.filter((_, i) => i !== idx))
  }

  const updateLine = (idx: number, patch: Partial<PaymentLine>) => {
    setLines((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)))
  }

  const handleCreatePayment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!studentId) return

    const imputations = lines
      .filter((l) => l.invoice_id && l.amount_cents)
      .map((l) => ({ invoice_id: l.invoice_id, amount_cents: parseInt(l.amount_cents, 10) }))

    if (imputations.length === 0) return

    const selectedInvoices = invoices.filter((inv) => imputations.some((imp) => imp.invoice_id === inv.id))
    const uniqueCurrencies = Array.from(new Set(selectedInvoices.map((i) => i.currency)))
    if (uniqueCurrencies.length > 1) {
      alert('All selected invoices must have the same currency')
      return
    }

    const cur = uniqueCurrencies[0] || currency

    if (!paymentMethod) {
      alert('Please select a payment method')
      return
    }

    setCreating(true)
    try {
      await paymentsApi.create({
        student_id: studentId,
        amount_cents: imputations.reduce((acc, imp) => acc + imp.amount_cents, 0),
        currency: cur,
        payment_method: paymentMethod,
        imputations,
      })
      setPaymentMethod('')
      setLines([{ invoice_id: '', amount_cents: '' }])
      await loadInvoices(studentId)
      alert('Payment created')
    } catch (err: any) {
      console.error(err)
      alert(err?.response?.data?.detail ?? 'Failed to create payment')
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Payments</h1>
          <p className="mt-2 text-sm text-gray-700">Create payments and impute them to invoices.</p>
        </div>
      </div>

      <div className="mt-6 bg-white shadow sm:rounded-lg p-6">
        <form onSubmit={handleCreatePayment}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Student</label>
              <select
                required
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
              >
                <option value="">Select a student</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Payment method</label>
              <select
                required
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
              >
                <option value="">Select payment method</option>
                {PAYMENT_METHODS.map((method) => (
                  <option key={method.value} value={method.value}>
                    {method.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="border rounded-md p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold text-gray-900">Imputations</div>
                <button
                  type="button"
                  onClick={addLine}
                  className="rounded-md bg-gray-100 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-200"
                >
                  Add line
                </button>
              </div>

              <div className="space-y-3">
                {lines.map((line, idx) => (
                  <div key={idx} className="grid grid-cols-1 sm:grid-cols-12 gap-2">
                    <div className="sm:col-span-7">
                      <select
                        value={line.invoice_id}
                        onChange={(e) => updateLine(idx, { invoice_id: e.target.value })}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                      >
                        <option value="">Select invoice</option>
                        {invoices.map((inv) => (
                          <option key={inv.id} value={inv.id}>
                            {inv.description || inv.id.slice(0, 8)} - {formatMoney(inv.amount_cents, inv.currency)}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="sm:col-span-4">
                      <input
                        type="number"
                        min="1"
                        placeholder="Amount (cents)"
                        value={line.amount_cents}
                        onChange={(e) => updateLine(idx, { amount_cents: e.target.value })}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                      />
                    </div>
                    <div className="sm:col-span-1 flex justify-end">
                      <button
                        type="button"
                        onClick={() => removeLine(idx)}
                        disabled={lines.length === 1}
                        className="rounded-md bg-red-50 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 disabled:opacity-50"
                      >
                        X
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-3 text-sm text-gray-700">
                Total: <span className="font-semibold">{formatMoney(totalCents, currency)}</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={creating}
              className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create Payment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
