import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ManageSkillsModal } from "../ManageSkillsModal";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

describe("ManageSkillsModal Component (#724)", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createTestQueryClient();
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("renders initial skills list and title", () => {
    const initialSkills = [
      { name: "TypeScript", category: "Languages", level: "Expert" },
      { name: "React", category: "Frameworks", level: "Advanced" },
    ];

    render(
      <ManageSkillsModal
        open={true}
        onOpenChange={vi.fn()}
        initialSkills={initialSkills}
      />,
      { wrapper },
    );

    expect(screen.getByText("Manage Skills")).toBeInTheDocument();
    expect(screen.getByText("TypeScript")).toBeInTheDocument();
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  it("adds a new skill to the list", () => {
    render(
      <ManageSkillsModal
        open={true}
        onOpenChange={vi.fn()}
        initialSkills={[{ name: "Python", category: "Languages" }]}
      />,
      { wrapper },
    );

    const input = screen.getByPlaceholderText("e.g. TypeScript, React, Docker");
    fireEvent.change(input, { target: { value: "FastAPI" } });

    const addBtn = screen.getByRole("button", { name: /^Add$/i });
    fireEvent.click(addBtn);

    expect(screen.getByText("FastAPI")).toBeInTheDocument();
  });

  it("prevents duplicate skills from being added", () => {
    render(
      <ManageSkillsModal
        open={true}
        onOpenChange={vi.fn()}
        initialSkills={[{ name: "TypeScript", category: "Languages" }]}
      />,
      { wrapper },
    );

    const input = screen.getByPlaceholderText("e.g. TypeScript, React, Docker");
    fireEvent.change(input, { target: { value: "typescript" } });

    const addBtn = screen.getByRole("button", { name: /^Add$/i });
    fireEvent.click(addBtn);

    expect(
      screen.getByText('"typescript" is already in your skills list.'),
    ).toBeInTheDocument();
  });

  it("reorders skills when Move Up or Move Down is clicked", () => {
    const initialSkills = [
      { name: "FirstSkill", category: "Languages" },
      { name: "SecondSkill", category: "Frameworks" },
    ];

    render(
      <ManageSkillsModal
        open={true}
        onOpenChange={vi.fn()}
        initialSkills={initialSkills}
      />,
      { wrapper },
    );

    const moveDownBtns = screen.getAllByTitle("Move Down");
    fireEvent.click(moveDownBtns[0]);

    // The order should now have SecondSkill first
    const skillCards = screen.getAllByText(/^(FirstSkill|SecondSkill)$/);
    expect(skillCards[0].textContent).toBe("SecondSkill");
    expect(skillCards[1].textContent).toBe("FirstSkill");
  });

  it("removes a skill when delete button is clicked", () => {
    const initialSkills = [{ name: "SkillToDelete", category: "Languages" }];

    render(
      <ManageSkillsModal
        open={true}
        onOpenChange={vi.fn()}
        initialSkills={initialSkills}
      />,
      { wrapper },
    );

    expect(screen.getByText("SkillToDelete")).toBeInTheDocument();

    const deleteBtn = screen.getByTitle("Delete skill");
    fireEvent.click(deleteBtn);

    expect(screen.queryByText("SkillToDelete")).not.toBeInTheDocument();
    expect(screen.getByText("No skills added yet")).toBeInTheDocument();
  });
});
