import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Login from "../pages/Login";

// Mock the Zustand useAppStore
const mockLogin = vi.fn().mockResolvedValue(undefined);
const mockRegister = vi.fn().mockResolvedValue(undefined);

vi.mock("@/store/useAppStore", () => ({
  useAppStore: () => ({
    login: mockLogin,
    register: mockRegister,
    settings: {
      isLoggedIn: false,
    },
  }),
}));

// Mock Framer Motion to bypass animation issues in tests
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe("Login Component Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the sign-in form by default", () => {
    const { container } = render(<Login />);
    
    // Check main headers
    expect(screen.getByText("Spend Sense")).toBeInTheDocument();
    expect(screen.getByText("Smart Wealth Intelligence")).toBeInTheDocument();
    
    // Check input fields
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    
    // Display name should not be present in Sign In tab
    expect(screen.queryByLabelText(/Display Name/i)).not.toBeInTheDocument();
    
    // Submit button should say Sign In
    const submitBtn = container.querySelector('button[type="submit"]');
    expect(submitBtn).toBeInTheDocument();
    expect(submitBtn).toHaveTextContent("Sign In");
  });

  it("switches to registration form when clicking Create Account tab", async () => {
    const { container } = render(<Login />);
    
    const createAccountTab = screen.getByRole("button", { name: /Create Account/i });
    fireEvent.click(createAccountTab);
    
    // Wait for the dynamic transition (or immediate mock render)
    expect(screen.getByLabelText(/Display Name/i)).toBeInTheDocument();
    expect(screen.getByText(/Profile Type/i)).toBeInTheDocument();
    
    // Submit button should switch to Register
    const submitBtn = container.querySelector('button[type="submit"]');
    expect(submitBtn).toBeInTheDocument();
    expect(submitBtn).toHaveTextContent("Register");
  });

  it("submits the sign-in details and calls the login action", async () => {
    const { container } = render(<Login />);
    
    const emailInput = screen.getByLabelText(/Email/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement;
    
    fireEvent.change(emailInput, { target: { value: "hacker@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "SecretPassword123!" } });
    fireEvent.click(submitBtn);
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("hacker@example.com", "SecretPassword123!");
    });
  });

  it("submits the register details and calls the register action", async () => {
    const { container } = render(<Login />);
    
    // Switch to register tab
    const createAccountTab = screen.getByRole("button", { name: /Create Account/i });
    fireEvent.click(createAccountTab);
    
    const nameInput = screen.getByLabelText(/Display Name/i);
    const emailInput = screen.getByLabelText(/Email/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement;
    
    fireEvent.change(nameInput, { target: { value: "Hacker User" } });
    fireEvent.change(emailInput, { target: { value: "hacker@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "SecretPassword123!" } });
    fireEvent.click(submitBtn);
    
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith("hacker@example.com", "SecretPassword123!", "Hacker User", "Professional");
    });
  });
});

