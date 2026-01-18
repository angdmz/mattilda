import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { accountStatementsApi, SchoolAccountStatement } from '../api/client'

export default function SchoolStatement() {
  const { schoolId } = useParams<{ schoolId: string }>()
  const [data, setData] = useState<SchoolAccountStatement | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    if (!schoolId) return
    load(schoolId)
  }, [schoolId])

  const load = async (id: string) => {
    try {
      const res = await accountStatementsApi.getSchoolStatement(id)
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
        <Link to="/" className="text-indigo-600 hover:text-indigo-900">
          Back to schools
        </Link>
      </div>

      <div className="bg-white shadow sm:rounded-lg p-6">
        <h1 className="text-2xl font-semibold text-gray-900">School account statement</h1>
        <div className="mt-2 text-sm text-gray-700">
          <div>School: <span className="font-semibold">{data.school_name}</span></div>
          <div>Students: <span className="font-semibold">{data.number_of_students}</span></div>
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
          <h2 className="text-lg font-semibold text-gray-900">Students</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-300">
              <thead>
                <tr>
                  <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-0">Student</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Outstanding</th>
                  <th className="relative py-3.5 pl-3 pr-4 sm:pr-0" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.students.map((s) => (
                  <tr key={s.student_id}>
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-0">
                      {s.student_name}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {formatMoney(s.total_outstanding.amount_cents, s.total_outstanding.currency)}
                    </td>
                    <td className="whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-0">
                      <button
                        onClick={() => navigate(`/students/${s.student_id}/statement`)}
                        className="text-indigo-600 hover:text-indigo-900"
                      >
                        View
                      </button>
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
