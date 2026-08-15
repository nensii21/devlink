import { expect, test } from "vitest";
import { hasPermission } from "../permissions";

test("owner has all permissions", () => {
  expect(hasPermission("owner", "organization:manage")).toBe(true);
  expect(hasPermission("owner", "members:manage")).toBe(true);
});

test("admin can manage members but not organizations", () => {
  expect(hasPermission("admin", "members:manage")).toBe(true);
  expect(hasPermission("admin", "organization:manage")).toBe(false);
});

test("recruiter can manage candidates but not members", () => {
  expect(hasPermission("recruiter", "candidates:manage")).toBe(true);
  expect(hasPermission("recruiter", "members:manage")).toBe(false);
});

test("member has basic view access only", () => {
  expect(hasPermission("member", "organization:view")).toBe(true);
  expect(hasPermission("member", "content:view")).toBe(true);
  expect(hasPermission("member", "members:manage")).toBe(false);
});
