import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { accountStatementsApi, StudentAccountStatement } from '../api/client'

export default function StudentStatement() {
  const { studentId } = useParams<{ studentId: string }>()
  const [data, setData] = useState<StudentAccountStatement | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!studentId) return
    load(studentId)
  }, [studentId])

  const load = async (id: string) => {
    try {
      const res = await accountStatementsApi.getStudentStatement(id)
      setData(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const formatMoney = (cents: number, currency: string) => `${currency} ${(cents / 100).toFixed(2)}`

  if (loading) return <div className="text-center py-8">Loading...</div>
  if (!data) return <div className="text-center py-8">Not found</div>

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-4">
        <Link to="/students" className="text-indigo-600 hover:text-indigo-900">
          Back to students
        </Link>
      </div>

      <div className="bg-white shadow sm:rounded-lg p-6">
        <h1 className="text-2xl font-semibold text-gray-900">Student account statement</h1>
        <div className="mt-2 text-sm text-gray-700">
          <div>Student: <span className="font-semibold">{data.student_name}</span></div>
          <div>School: <span className="font-semibold">{data.school_name}</span></div>
        </div>

        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-md bg-gray-50 p-4">
            <div className="text-sm text-gray-500">Total invoiced</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatMoney(data.total_invoiced.amount_cents, data.total_invoiced.currency)}
            </div>
          </div>
          <div className="rounded-md bg-gray-50 p-4">
            <div className="text-sm text-gray-500">Total paid</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatMoney(data.total_paid.amount_cents, data.total_paid.currency)}
            </div>
          </div>
          <div className="rounded-md bg-gray-50 p-4">
            <div className="text-sm text-gray-500">Outstanding</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatMoney(data.total_outstanding.amount_cents, data.total_outstanding.currency)}
            </div>
          </div>
        </div>

        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900">Invoices</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-300">
              <thead>
                <tr>
                  <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-0">Issued</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Description</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Amount</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Paid</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Outstanding</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.invoices.map((inv) => (
                  <tr key={inv.id}>
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm text-gray-900 sm:pl-0">
                      {new Date(inv.issued_at).toLocaleDateString()}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{inv.description || '-'}</td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {formatMoney(inv.amount.amount_cents, inv.amount.currency)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {formatMoney(inv.paid_amount.amount_cents, inv.paid_amount.currency)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {formatMoney(inv.outstanding_amount.amount_cents, inv.outstanding_amount.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
