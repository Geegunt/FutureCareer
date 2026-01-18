export type Vacancy = {
  id: string
  title: string
  position: string
  language: string
  grade: string
  ideal_resume: string
  created_at: string
  updated_at: string
}

export type Application = {
  id: string
  user_id: string
  vacancy_id: string
  ml_score: number | null
  status: 'pending' | 'survey_completed' | 'algo_test_completed' | 'under_review' | 'accepted' | 'rejected' | 'final_verdict'
  started_at: string | null
  completed_at: string | null
  time_limit_minutes: number
  created_at: string
  updated_at: string
  vacancy?: Vacancy | null  // Информация о вакансии
  user?: {
    id: string
    email: string
    full_name: string | null
  } | null  // Информация о пользователе (для модератора)
}

