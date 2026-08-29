import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { TestimonialsSection, DEFAULT_TESTIMONIALS } from "../TestimonialsSection";

describe("TestimonialsSection Component (#762)", () => {
  it("renders header title, subtitle, and developer testimonials", () => {
    render(<TestimonialsSection />);

    expect(
      screen.getByRole("heading", { name: /loved by developers & contributors/i })
    ).toBeInTheDocument();

    expect(
      screen.getByText(/see how builders use devlink to find teammates/i)
    ).toBeInTheDocument();

    // Check first default testimonial details
    expect(screen.getAllByText("Sarah Chen")[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Senior Full Stack Engineer/i)[0]).toBeInTheDocument();
    expect(
      screen.getAllByText(/DevLink matched me with two incredible co-builders/i)[0]
    ).toBeInTheDocument();
  });

  it("renders user avatar, role, company, and quote for provided testimonials", () => {
    const customTestimonials = [
      {
        id: "t1",
        name: "Alex Rivera",
        role: "Lead Systems Engineer",
        company: "Nexus Labs",
        avatar: "https://example.com/avatar.jpg",
        quote: "DevLink revolutionized our team matching process!",
        rating: 5,
        badge: "Top Contributor",
      },
    ];

    render(<TestimonialsSection testimonials={customTestimonials} />);

    expect(screen.getAllByText("Alex Rivera")[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Lead Systems Engineer • Nexus Labs/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/"DevLink revolutionized our team matching process!"/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText("Top Contributor")[0]).toBeInTheDocument();
  });

  it("supports carousel navigation with previous and next buttons", () => {
    render(<TestimonialsSection testimonials={DEFAULT_TESTIMONIALS} />);

    const nextBtn = screen.getByRole("button", { name: /next testimonial/i });
    const prevBtn = screen.getByRole("button", { name: /previous testimonial/i });

    expect(nextBtn).toBeInTheDocument();
    expect(prevBtn).toBeInTheDocument();

    // Click next button
    fireEvent.click(nextBtn);

    // Click previous button
    fireEvent.click(prevBtn);
  });

  it("provides accessible ARIA region and navigation roles", () => {
    render(<TestimonialsSection />);

    const section = screen.getByRole("region", { name: /developer testimonials carousel/i });
    expect(section).toBeInTheDocument();

    const dots = screen.getAllByRole("button", { name: /go to testimonial/i });
    expect(dots.length).toBe(DEFAULT_TESTIMONIALS.length);
  });
});
