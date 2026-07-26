import { describe, it, expect } from "vitest";
import {
  loginSchema,
  signupSchema,
  profileSchema,
  createProjectSchema,
  accountSettingsSchema,
  changePasswordSchema,
} from "../forms";

describe("Form Validation Schemas", () => {
  // ------------------------------------------------------------------
  // 1. LOGIN FORM TESTS
  // ------------------------------------------------------------------
  describe("Login Form (loginSchema)", () => {
    it("should fail validation when required fields are empty", () => {
      const result = loginSchema.safeParse({ email: "", password: "" });
      expect(result.success).toBe(false);
      if (!result.success) {
        const fieldErrors = result.error.flatten().fieldErrors;
        expect(fieldErrors.email).toBeDefined();
        expect(fieldErrors.password).toBeDefined();
      }
    });

    it("should fail validation when invalid inputs are provided", () => {
      // Invalid email format
      const invalidEmail = loginSchema.safeParse({
        email: "not-an-email",
        password: "Password123!",
      });
      expect(invalidEmail.success).toBe(false);
      if (!invalidEmail.success) {
        expect(invalidEmail.error.flatten().fieldErrors.email).toContain("Enter a valid email");
      }

      // Password too short (< 8 chars)
      const shortPassword = loginSchema.safeParse({
        email: "user@example.com",
        password: "123",
      });
      expect(shortPassword.success).toBe(false);
      if (!shortPassword.success) {
        expect(shortPassword.error.flatten().fieldErrors.password).toContain(
          "At least 8 characters",
        );
      }
    });

    it("should pass validation with valid inputs for successful submission", () => {
      const validData = {
        email: "user@example.com",
        password: "Password123!",
      };
      const result = loginSchema.safeParse(validData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validData);
      }
    });
  });

  // ------------------------------------------------------------------
  // 2. SIGNUP FORM TESTS
  // ------------------------------------------------------------------
  describe("Signup Form (signupSchema)", () => {
    it("should fail validation when required fields are missing or empty", () => {
      const result = signupSchema.safeParse({
        first_name: "",
        last_name: "",
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const fieldErrors = result.error.flatten().fieldErrors;
        expect(fieldErrors.first_name).toBeDefined();
        expect(fieldErrors.last_name).toBeDefined();
        expect(fieldErrors.username).toBeDefined();
        expect(fieldErrors.email).toBeDefined();
        expect(fieldErrors.password).toBeDefined();
      }
    });

    it("should fail validation for invalid inputs", () => {
      // Short first/last names & invalid username regex & short password
      const result = signupSchema.safeParse({
        first_name: "A",
        last_name: "B",
        username: "invalid-username!", // contains hyphens & exclamation
        email: "invalid-email",
        password: "short",
        confirmPassword: "differentPassword",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const fieldErrors = result.error.flatten().fieldErrors;
        expect(fieldErrors.first_name).toContain("At least 2 characters");
        expect(fieldErrors.last_name).toContain("At least 2 characters");
        expect(fieldErrors.username).toContain("Letters, numbers, and underscores only");
        expect(fieldErrors.email).toContain("Enter a valid email");
        expect(fieldErrors.password).toContain("At least 8 characters");
        expect(fieldErrors.confirmPassword).toContain("Passwords must match");
      }
    });

    it("should pass validation with valid inputs for successful submission", () => {
      const validData = {
        first_name: "Jane",
        last_name: "Doe",
        username: "janedoe99",
        email: "jane.doe@example.com",
        password: "SecurePassword123!",
        confirmPassword: "SecurePassword123!",
      };
      const result = signupSchema.safeParse(validData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validData);
      }
    });
  });

  // ------------------------------------------------------------------
  // 3. PROFILE FORM TESTS
  // ------------------------------------------------------------------
  describe("Profile Form (profileSchema)", () => {
    it("should fail validation when required fields are missing", () => {
      const result = profileSchema.safeParse({
        first_name: "",
        last_name: "",
        username: "",
        email: "",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const fieldErrors = result.error.flatten().fieldErrors;
        expect(fieldErrors.first_name).toBeDefined();
        expect(fieldErrors.last_name).toBeDefined();
        expect(fieldErrors.username).toBeDefined();
        expect(fieldErrors.email).toBeDefined();
      }
    });

    it("should fail validation for invalid inputs (bad URLs, bio over length limit)", () => {
      const result = profileSchema.safeParse({
        first_name: "John",
        last_name: "Smith",
        username: "john_smith",
        email: "john@example.com",
        bio: "a".repeat(1001), // > 1000 characters
        website: "not-a-url",
        github_url: "invalid-github-url",
        linkedin_url: "invalid-linkedin-url",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const fieldErrors = result.error.flatten().fieldErrors;
        expect(fieldErrors.bio).toContain("Bio cannot exceed 1000 characters");
        expect(fieldErrors.website).toContain("Must be a valid URL");
        expect(fieldErrors.github_url).toContain("Must be a valid URL");
        expect(fieldErrors.linkedin_url).toContain("Must be a valid URL");
      }
    });

    it("should pass validation with valid inputs for successful submission", () => {
      const validData = {
        first_name: "John",
        last_name: "Smith",
        username: "john_smith",
        email: "john@example.com",
        bio: "Full stack developer passionate about open source.",
        website: "https://johnsmith.dev",
        github_url: "https://github.com/johnsmith",
        linkedin_url: "https://linkedin.com/in/johnsmith",
      };
      const result = profileSchema.safeParse(validData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validData);
      }
    });
  });

  // ------------------------------------------------------------------
  // 4. CREATE PROJECT FORM TESTS
  // ------------------------------------------------------------------
  describe("Create Project Form (createProjectSchema)", () => {
    it("should fail validation when required fields are missing", () => {
      const result = createProjectSchema.safeParse({
        title: "",
        description: "",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const fieldErrors = result.error.flatten().fieldErrors;
        expect(fieldErrors.title).toBeDefined();
        expect(fieldErrors.description).toBeDefined();
      }
    });

    it("should fail validation for invalid inputs", () => {
      const result = createProjectSchema.safeParse({
        title: "AB", // < 3 chars
        tagline: "a".repeat(151), // > 150 chars
        description: "Short", // < 10 chars
        stage: "unknown_stage", // invalid enum
        repository_url: "bad-repo-url",
        demo_url: "bad-demo-url",
        max_team_size: 0, // < 1
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const fieldErrors = result.error.flatten().fieldErrors;
        expect(fieldErrors.title).toContain("Title must be at least 3 characters");
        expect(fieldErrors.tagline).toContain("Tagline cannot exceed 150 characters");
        expect(fieldErrors.description).toContain("Description must be at least 10 characters");
        expect(fieldErrors.stage).toContain("Invalid project stage");
        expect(fieldErrors.repository_url).toContain("Must be a valid URL");
        expect(fieldErrors.demo_url).toContain("Must be a valid URL");
        expect(fieldErrors.max_team_size).toContain("Team size must be at least 1");
      }
    });

    it("should pass validation with valid inputs for successful submission", () => {
      const validData = {
        title: "DevLink Platform",
        tagline: "Developer showcase and collaboration platform",
        description: "A comprehensive web application for developers to build and share.",
        stage: "beta" as const,
        tech_stack: "React, TypeScript, FastAPI, PostgreSQL",
        repository_url: "https://github.com/example/devlink",
        demo_url: "https://devlink.example.com",
        max_team_size: 10,
      };
      const result = createProjectSchema.safeParse(validData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validData);
      }
    });
  });

  // ------------------------------------------------------------------
  // 5. SETTINGS FORM TESTS
  // ------------------------------------------------------------------
  describe("Settings Forms", () => {
    describe("Account Settings Form (accountSettingsSchema)", () => {
      it("should fail validation when required fields are empty", () => {
        const result = accountSettingsSchema.safeParse({
          name: "",
          username: "",
          email: "",
        });
        expect(result.success).toBe(false);
        if (!result.success) {
          const fieldErrors = result.error.flatten().fieldErrors;
          expect(fieldErrors.name).toBeDefined();
          expect(fieldErrors.username).toBeDefined();
          expect(fieldErrors.email).toBeDefined();
        }
      });

      it("should fail validation for invalid inputs", () => {
        const result = accountSettingsSchema.safeParse({
          name: "A",
          username: "user@invalid",
          email: "not-an-email",
          bio: "x".repeat(1001),
        });
        expect(result.success).toBe(false);
        if (!result.success) {
          const fieldErrors = result.error.flatten().fieldErrors;
          expect(fieldErrors.name).toContain("At least 2 characters");
          expect(fieldErrors.username).toContain("Letters, numbers, and underscores only");
          expect(fieldErrors.email).toContain("Enter a valid email");
          expect(fieldErrors.bio).toContain("Bio cannot exceed 1000 characters");
        }
      });

      it("should pass validation with valid inputs for successful submission", () => {
        const validData = {
          name: "Nancy Wheeler",
          username: "nancy_w",
          email: "nancy@devlink.io",
          bio: "Product engineer. React / Postgres / Rust.",
        };
        const result = accountSettingsSchema.safeParse(validData);
        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.data).toEqual(validData);
        }
      });
    });

    describe("Change Password Form (changePasswordSchema)", () => {
      it("should fail validation when required fields are empty", () => {
        const result = changePasswordSchema.safeParse({
          current_password: "",
          new_password: "",
          confirm_new_password: "",
        });
        expect(result.success).toBe(false);
        if (!result.success) {
          const fieldErrors = result.error.flatten().fieldErrors;
          expect(fieldErrors.current_password).toBeDefined();
          expect(fieldErrors.new_password).toBeDefined();
          expect(fieldErrors.confirm_new_password).toBeDefined();
        }
      });

      it("should fail validation when new password is too short or confirmation mismatch", () => {
        const result = changePasswordSchema.safeParse({
          current_password: "OldPassword123!",
          new_password: "short",
          confirm_new_password: "different",
        });
        expect(result.success).toBe(false);
        if (!result.success) {
          const fieldErrors = result.error.flatten().fieldErrors;
          expect(fieldErrors.new_password).toContain("New password must be at least 8 characters");
          expect(fieldErrors.confirm_new_password).toContain("New passwords must match");
        }
      });

      it("should pass validation with valid inputs for successful submission", () => {
        const validData = {
          current_password: "OldPassword123!",
          new_password: "NewSecurePassword456!",
          confirm_new_password: "NewSecurePassword456!",
        };
        const result = changePasswordSchema.safeParse(validData);
        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.data).toEqual(validData);
        }
      });
    });
  });
});
