export interface Specifier {
  id: string
  email: string
  first_name: string
  last_name: string
  firm_name: string
  role: string
  country?: string
  phone?: string
  specialization?: string
  verified: boolean
  created_at: string
}

export interface Manufacturer {
  id: string
  name: string
  slug: string
  country: string
  website?: string
  description?: string
}

export interface Product {
  id: string
  manufacturer_id: string
  manufacturer_name: string
  manufacturer?: Manufacturer
  sku: string
  name: string
  slug: string
  category: string
  subcategory?: string | null
  collection?: string | null
  description?: string
  fire_class_eu?: string | null
  fire_smoke_class_eu?: string | null
  fire_droplet_class_eu?: string | null
  nrc_value?: string | null
  acoustic_nrc?: number
  acoustic_class?: string | null
  commercial_grade?: string[]
  width_mm?: number
  height_mm?: number
  thickness_mm?: number
  weight_value?: number
  weight_unit?: string
  lead_time_weeks?: number
  lead_time_weeks_min?: number
  lead_time_weeks_max?: number | null
  moq?: number
  moq_unit?: string
  price_per_unit?: number
  indicative_price_eur?: string | null
  price_unit?: string | null
  price_currency?: string
  price_visibility?: string
  custom_colorway?: boolean
  colorway_count?: number
  sample_available?: boolean
  sample_type?: string | null
  images?: ProductImage[]
  certifications?: ProductCertification[]
  primary_image_url?: string | null
  is_featured?: boolean
}

export interface ProductImage {
  id: string
  url: string
  alt_text?: string
  is_primary: boolean
  sort_order: number
}

export interface ProductCertification {
  id: string
  certification_code: string
  certification_body?: string
  certificate_number?: string
  valid_until?: string
}

export interface Project {
  id: string
  name: string
  description?: string
  is_shared: boolean
  share_token?: string
  created_at: string
  updated_at: string
  products?: ProjectProduct[]
}

export interface ProjectProduct {
  id: string
  product_id: string
  product?: Product
  notes?: string
  quantity?: number
  added_at: string
}

export interface AuthResponse {
  message: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  specifier: Specifier
}
