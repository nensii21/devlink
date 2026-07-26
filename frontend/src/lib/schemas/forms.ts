import { z } from "zod";

// Helper for optional URL fields that allow empty string
const optionalUrl = z
  .string()
  .optional()
  .refine((val) => !val || val.trim() === "" || z.string().url().safeParse(val).success, {
    message: "Must be a valid URL",
  });

// 1. Login Form Schema
export const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email"),
  password: z.string().min(1, "Password is required").min(8, "At least 8 characters"),
});

export type LoginFormData = z.infer<typeof loginSchema>;

// 2. Signup Form Schema
export const signupSchema = z
  .object({
    first_name: z
      .string()
      .min(1, "First name is required")
      .min(2, "At least 2 characters")
      .max(100, "At most 100 characters"),
    last_name: z
      .string()
      .min(1, "Last name is required")
      .min(2, "At least 2 characters")
      .max(100, "At most 100 characters"),
    username: z
      .string()
      .min(1, "Username is required")
      .min(3, "At least 3 characters")
      .max(50, "At most 50 characters")
      .regex(/^[a-zA-Z0-9_]+$/, "Letters, numbers, and underscores only"),
    email: z.string().min(1, "Email is required").email("Enter a valid email"),
    password: z.string().min(1, "Password is required").min(8, "At least 8 characters"),
    confirmPassword: z.string().min(1, "Confirm password is required"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords must match",
    path: ["confirmPassword"],
  });

export type SignupFormData = z.infer<typeof signupSchema>;

// 3. Profile Form Schema
export const profileSchema = z.object({
  first_name: z
    .string()
    .min(1, "First name is required")
    .min(2, "At least 2 characters")
    .max(100, "At most 100 characters"),
  last_name: z
    .string()
    .min(1, "Last name is required")
    .min(2, "At least 2 characters")
    .max(100, "At most 100 characters"),
  username: z
    .string()
    .min(1, "Username is required")
    .min(3, "At least 3 characters")
    .max(50, "At most 50 characters")
    .regex(/^[a-zA-Z0-9_]+$/, "Letters, numbers, and underscores only"),
  email: z.string().min(1, "Email is required").email("Enter a valid email"),
  bio: z.string().max(1000, "Bio cannot exceed 1000 characters").optional(),
  website: optionalUrl,
  github_url: optionalUrl,
  linkedin_url: optionalUrl,
});

export type ProfileFormData = z.infer<typeof profileSchema>;

// 4. Create Project Form Schema
export const createProjectSchema = z.object({
  title: z
    .string()
    .min(1, "Title is required")
    .min(3, "Title must be at least 3 characters")
    .max(100, "Title cannot exceed 100 characters"),
  tagline: z.string().max(150, "Tagline cannot exceed 150 characters").optional(),
  description: z
    .string()
    .min(1, "Description is required")
    .min(10, "Description must be at least 10 characters"),
  stage: z.enum(["idea", "in_development", "beta", "launched"], {
    errorMap: () => ({ message: "Invalid project stage" }),
  }),
  tech_stack: z.string().optional(),
  repository_url: optionalUrl,
  demo_url: optionalUrl,
  max_team_size: z
    .number({ invalid_type_error: "Team size must be a number" })
    .min(1, "Team size must be at least 1")
    .max(100, "Team size cannot exceed 100"),
});

export type CreateProjectFormData = z.infer<typeof createProjectSchema>;

// 5. Settings Form Schemas (Account Settings & Change Password)
export const accountSettingsSchema = z.object({
  name: z.string().min(1, "Full name is required").min(2, "At least 2 characters"),
  username: z
    .string()
    .min(1, "Username is required")
    .min(3, "At least 3 characters")
    .max(50, "At most 50 characters")
    .regex(/^[a-zA-Z0-9_]+$/, "Letters, numbers, and underscores only"),
  email: z.string().min(1, "Email is required").email("Enter a valid email"),
  bio: z.string().max(1000, "Bio cannot exceed 1000 characters").optional(),
});

export type AccountSettingsFormData = z.infer<typeof accountSettingsSchema>;

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required"),
    new_password: z
      .string()
      .min(1, "New password is required")
      .min(8, "New password must be at least 8 characters"),
    confirm_new_password: z.string().min(1, "Please confirm your new password"),
  })
  .refine((data) => data.new_password === data.confirm_new_password, {
    message: "New passwords must match",
    path: ["confirm_new_password"],
  });

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;
