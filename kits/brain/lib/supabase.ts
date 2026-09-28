import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

/**
 * Public client — use on the client side (browser).
 * Row-level security (RLS) applies.
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

/**
 * Admin client — use in API routes only (server-side).
 * Bypasses RLS. Requires SERVICE_ROLE_KEY in .env.local.
 */
export const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey);

export type { SupabaseClient } from "@supabase/supabase-js";
