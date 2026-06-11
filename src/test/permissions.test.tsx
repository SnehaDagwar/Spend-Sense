import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import FamilyMembers from "../pages/family/FamilyMembers";

// Mock the Zustand useAppStore
const mockAddFamilyMember = vi.fn();
const mockRemoveFamilyMember = vi.fn();

const mockMembers = [
  { id: "1", name: "Sarah Owner", role: "Admin" as const },
  { id: "2", name: "David Member", role: "Member" as const },
  { id: "3", name: "Emily Child", role: "Child" as const },
];

vi.mock("@/store/useAppStore", () => ({
  useAppStore: () => ({
    familyMembers: mockMembers,
    addFamilyMember: mockAddFamilyMember,
    removeFamilyMember: mockRemoveFamilyMember,
  }),
}));

// Mock Framer Motion
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe("FamilyMembers Component Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the members list with their roles", () => {
    render(<FamilyMembers />);
    
    // Header check
    expect(screen.getByText("Family Members")).toBeInTheDocument();
    
    // Check rendered members
    expect(screen.getByText("Sarah Owner")).toBeInTheDocument();
    expect(screen.getByText("David Member")).toBeInTheDocument();
    expect(screen.getByText("Emily Child")).toBeInTheDocument();
    
    // Check roles representation
    expect(screen.getAllByText("Admin").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Member").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Child").length).toBeGreaterThan(0);
  });

  it("opens the Add New Member dialog on clicking Add Member button", () => {
    render(<FamilyMembers />);
    
    const addBtn = screen.getByRole("button", { name: /Add Member/i });
    fireEvent.click(addBtn);
    
    expect(screen.getByText("Add New Member")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. Sarah")).toBeInTheDocument();
  });

  it("triggers addFamilyMember when inputting details and clicking Add", () => {
    render(<FamilyMembers />);
    
    // Open panel
    fireEvent.click(screen.getByRole("button", { name: /Add Member/i }));
    
    // Input fields
    const nameInput = screen.getByPlaceholderText("e.g. Sarah");
    const submitBtn = screen.getByRole("button", { name: /^Add$/i });
    
    fireEvent.change(nameInput, { target: { value: "Uncle Bob" } });
    fireEvent.click(submitBtn);
    
    expect(mockAddFamilyMember).toHaveBeenCalledWith({
      name: "Uncle Bob",
      role: "Member",
    });
  });

  it("displays removal action only for non-Admin members", () => {
    render(<FamilyMembers />);
    
    // Admin (Sarah Owner) should NOT have a delete button next to it.
    // In our component, only member.role !== "Admin" gets a remove button.
    // Let's verify the trash buttons correspond to non-admin roles.
    const removeButtons = screen.getAllByRole("button");
    // There are: Add Member, Add, Cancel (if open), but we didn't open.
    // So there is Add Member + remove buttons for plain members (David, Emily).
    // Total buttons should be 3: 1 for adding, 2 for removing.
    expect(removeButtons.length).toBe(3);
  });
});
