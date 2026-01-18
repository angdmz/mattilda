import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface School {
  id: string
  name: string
  address?: string
}

export interface Student {
  id: string
  name: string
  email?: string
  school_id: string
}

export interface Invoice {
  id: string
  student_id: string
  amount_cents: number
  currency: string
  description?: string
  issued_at: string
  due_date?: string
}

export interface Payment {
  id: string
  student_id: string
  amount_cents: number
  currency: string
  payment_date: string
  payment_method?: string
  reference?: string
}

export interface MoneyAmount {
  amount_cents: number
  currency: string
}

export interface InvoiceDetail {
  id: string
  amount: MoneyAmount
  paid_amount: MoneyAmount
  outstanding_amount: MoneyAmount
  issued_at: string
  description?: string
}

export interface StudentAccountStatement {
  student_id: string
  student_name: string
  school_id: string
  school_name: string
  total_invoiced: MoneyAmount
  total_paid: MoneyAmount
  total_outstanding: MoneyAmount
  invoices: InvoiceDetail[]
}

export interface StudentSummary {
  student_id: string
  student_name: string
  total_outstanding: MoneyAmount
}

export interface SchoolAccountStatement {
  school_id: string
  school_name: string
  total_invoiced: MoneyAmount
  total_paid: MoneyAmount
  total_outstanding: MoneyAmount
  number_of_students: number
  students: StudentSummary[]
}

export const schoolsApi = {
  list: () => apiClient.get<School[]>('/schools/'),
  get: (id: string) => apiClient.get<School>(`/schools/${id}`),
  create: (data: Omit<School, 'id'>) => apiClient.post<School>('/schools/', data),
  update: (id: string, data: Partial<Omit<School, 'id'>>) => apiClient.put<School>(`/schools/${id}`, data),
  delete: (id: string) => apiClient.delete(`/schools/${id}`),
}

export const studentsApi = {
  list: (schoolId?: string) => apiClient.get<Student[]>('/students/', { params: { school_id: schoolId } }),
  get: (id: string) => apiClient.get<Student>(`/students/${id}`),
  create: (data: Omit<Student, 'id'>) => apiClient.post<Student>('/students/', data),
  update: (id: string, data: Partial<Omit<Student, 'id'>>) => apiClient.put<Student>(`/students/${id}`, data),
  delete: (id: string) => apiClient.delete(`/students/${id}`),
}

export const invoicesApi = {
  list: (studentId?: string) => apiClient.get<Invoice[]>('/invoices/', { params: { student_id: studentId } }),
  get: (id: string) => apiClient.get<Invoice>(`/invoices/${id}`),
  create: (data: Omit<Invoice, 'id' | 'issued_at'>) => apiClient.post<Invoice>('/invoices/', data),
  update: (id: string, data: Partial<Omit<Invoice, 'id' | 'student_id' | 'issued_at'>>) => apiClient.put<Invoice>(`/invoices/${id}`, data),
  delete: (id: string) => apiClient.delete(`/invoices/${id}`),
}

export const paymentsApi = {
  list: (studentId?: string) => apiClient.get<Payment[]>('/payments/', { params: { student_id: studentId } }),
  get: (id: string) => apiClient.get<Payment>(`/payments/${id}`),
  create: (data: any) => apiClient.post<Payment>('/payments/', data),
  delete: (id: string) => apiClient.delete(`/payments/${id}`),
}

export const accountStatementsApi = {
  getStudentStatement: (studentId: string) => apiClient.get<StudentAccountStatement>(`/account-statements/students/${studentId}`),
  getSchoolStatement: (schoolId: string) => apiClient.get<SchoolAccountStatement>(`/account-statements/schools/${schoolId}`),
}
