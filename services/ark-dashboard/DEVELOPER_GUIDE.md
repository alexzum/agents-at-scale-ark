# Ark Dashboard Developer Guide

Welcome to the Ark Dashboard development guide. This document outlines the architectural decisions, best practices, and conventions used in the dashboard application.

## Table of Contents

1. [Component Library](#component-library)
2. [Folder Structure](#folder-structure)
3. [Forms](#forms)
4. [API Calls](#api-calls)
5. [Code Style](#code-style)
6. [Validations](#validations)
7. [Examples](#examples)

## Component Library

We use **[shadcn/ui](https://ui.shadcn.com/)** as our primary component library. Shadcn provides a collection of copy-paste components that you own and can customize.

### Configuration

The shadcn configuration is defined in `components.json`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
```

### Key Benefits

- **Customizable**: Components are copied into your codebase, so you have full control
- **Consistent**: Built on Radix UI primitives for accessibility and behavior
- **Tailwind Integration**: Seamless integration with Tailwind CSS
- **Type Safe**: Full TypeScript support

### Important Rule: Use Existing Components

**Do NOT create custom components for functionality that shadcn already provides.** Always check [the shadcn/ui documentation](https://ui.shadcn.com/docs/components) before building something from scratch.

#### ✅ Do This:
- Check if shadcn has a component for your use case
- Use the shadcn component as-is or customize it through props
- Extend existing shadcn components using composition

#### ❌ Don't Do This:
- Build a custom dropdown when shadcn has `Select` or `DropdownMenu`
- Create a custom modal when shadcn has `Dialog`
- Build custom form inputs when shadcn has `Input`, `Textarea`, etc.

### Adding New Components

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add form
npx shadcn-ui@latest add input
```

## Folder Structure

The dashboard follows a clear separation of concerns with the following structure:

```
ark-dashboard/
├── app/                    # Next.js app router pages
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── forms/            # Form-specific components
│   ├── auth/             # Authentication components
│   ├── chat/             # Chat-related components
│   └── ...               # Feature-specific folders
├── lib/                   # Non-React utilities and services
│   ├── api/              # API client and types
│   ├── services/         # API service functions
│   ├── utils/            # Pure utility functions
│   ├── types/            # TypeScript type definitions
│   └── constants/        # Application constants
├── hooks/                 # Custom React hooks
├── providers/            # React context providers
└── public/               # Static assets
```

### Important Rules

#### `/lib` Folder Guidelines

The `lib` folder should **NOT** contain React-specific code. It should only contain:

- ✅ Pure utility functions
- ✅ API service functions
- ✅ Type definitions
- ✅ Constants
- ✅ Configuration objects
- ❌ React components
- ❌ React hooks (use `/hooks` folder instead)
- ❌ JSX/TSX files (except for type definitions)

#### Component Organization

- **`/components/ui`**: shadcn/ui components and our own atomic/primitive components
- **`/components/forms`**: Form-specific components
- **`/components/pages`**: Page-specific components organized by route
- **`/components/[feature]`**: Feature-specific components (e.g., chat, auth, evaluation)

#### Page Organization

Pages in the `/app` router should be **as simple as possible** and only handle:
- Route definitions
- Server-side data fetching (if needed)
- Basic layout structure
- Delegating to page components

The actual page content should live in `/components/pages/[page-name]` folders.

**Example Structure:**
```
app/
├── users/
│   └── page.tsx           # Simple, delegates to UsersPage component
└── settings/
    └── page.tsx           # Simple, delegates to SettingsPage component

components/pages/
├── users/
│   ├── UsersPage.tsx      # Main page component
│   ├── UsersList.tsx      # Sub-components
│   └── UserActions.tsx
└── settings/
    ├── SettingsPage.tsx   # Main page component
    └── SettingsForm.tsx   # Sub-components
```

**Example App Router Page:**
```tsx
// app/users/page.tsx
import { UsersPage } from "@/components/pages/users/UsersPage";

export default function Page() {
  return <UsersPage />;
}
```

**Example Page Component:**
```tsx
// components/pages/users/UsersPage.tsx
"use client";

import { UsersList } from "./UsersList";
import { UserActions } from "./UserActions";

export function UsersPage() {
  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Users</h1>
        <UserActions />
      </div>
      <UsersList />
    </div>
  );
}
```

## Forms

We use **React Hook Form** for all form handling, which is the recommended solution by shadcn and provides excellent performance and developer experience.

### Key Dependencies

```json
{
  "react-hook-form": "^7.63.0",
  "@hookform/resolvers": "^5.2.2"
}
```

### Basic Form Structure

```tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Invalid email address"),
});

type FormData = z.infer<typeof formSchema>;

export function MyForm() {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      email: "",
    },
  });

  const onSubmit = (data: FormData) => {
    console.log(data);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  );
}
```

### Form Best Practices

1. **Always use Zod schemas** for validation
2. **Use zodResolver** for seamless integration
3. **Define TypeScript types** from Zod schemas using `z.infer<>`
4. **Validate on submit** - forms should validate when the user submits, not on every keystroke
5. **Keep submit button enabled** - only disable during submission in progress, not for validation errors
6. **Handle loading states** during form submission
7. **Provide clear error messages**
8. **Use defaultValues** for better UX

## API Calls

We use **[React Query](https://tanstack.com/query/latest)** (TanStack Query) for all API calls, which provides excellent caching, synchronization, and error handling.

### Key Dependencies

```json
{
  "@tanstack/react-query": "^5.87.1"
}
```

### Service Layer Structure

API calls are organized across two folders:

```
lib/services/
├── index.ts              # Export all services
└── [resource].ts         # API service functions (pure functions)

hooks/
└── [resource]-hooks.ts   # React Query hooks (React-specific)
```

### Generated Types

We generate TypeScript types from our OpenAPI specification. These types are automatically generated and should be used in the service layer:

```bash
npm run generate:api
```

This generates types in `/lib/api/generated/types.ts` from the OpenAPI spec.

### API Service Example

**Always use generated types** from the OpenAPI specification instead of defining your own interfaces:

```typescript
// lib/services/users.ts
import { apiClient } from '@/lib/api/client';
// Import generated types from OpenAPI spec
import type { 
  User, 
  CreateUserRequest, 
  UpdateUserRequest,
  UsersListResponse 
} from '@/lib/api/generated/types';

export const usersService = {
  list: async (): Promise<UsersListResponse> => {
    const response = await apiClient.get('/users');
    return response.data;
  },

  getById: async (id: string): Promise<User> => {
    const response = await apiClient.get(`/users/${id}`);
    return response.data;
  },

  create: async (data: CreateUserRequest): Promise<User> => {
    const response = await apiClient.post('/users', data);
    return response.data;
  },

  update: async (id: string, data: UpdateUserRequest): Promise<User> => {
    const response = await apiClient.patch(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/users/${id}`);
  },
};
```

### React Query Hooks Example

```typescript
// hooks/users-hooks.ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { usersService } from "@/lib/services/users";
import type { User, CreateUserRequest, UpdateUserRequest } from "@/lib/api/generated/types";

// Extract query keys into constants for reusability
export const usersQueryKeys = {
  all: ['users'],
  lists: () => [...usersQueryKeys.all, 'list'],
  list: (filters: string) => [...usersQueryKeys.lists(), { filters }],
  details: () => [...usersQueryKeys.all, 'detail'],
  detail: (id: string) => [...usersQueryKeys.details(), id],
};

export const useListUsers = () => {
  return useQuery({
    queryKey: usersQueryKeys.lists(),
    queryFn: usersService.list,
  });
};

export const useGetUser = (id: string) => {
  return useQuery({
    queryKey: usersQueryKeys.detail(id),
    queryFn: () => usersService.getById(id),
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: usersService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: usersQueryKeys.all });
    },
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserRequest }) =>
      usersService.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: usersQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: usersQueryKeys.detail(data.id) });
    },
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: usersService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: usersQueryKeys.all });
    },
  });
};
```

### Generated Types Best Practices

1. **Always use generated types** - Never manually define API types that exist in the generated file
2. **Import types with `type` keyword** - Use `import type { ... }` for type-only imports
3. **Regenerate after API changes** - Run `npm run generate:api` after backend API updates
4. **Don't modify generated files** - Generated types are overwritten on each generation
5. **Use generated types consistently** - Ensure all service functions use the same generated types

#### ✅ Do This:
```typescript
import type { User, CreateUserRequest } from '@/lib/api/generated/types';
```

#### ❌ Don't Do This:
```typescript
// Don't manually define types that exist in generated file
interface User {
  id: string;
  name: string;
  email: string;
}
```

### React Query Best Practices

1. **Use consistent query keys** following a hierarchical pattern
2. **Extract query keys into constants** for reusability and consistency
3. **Enable/disable queries** based on dependencies
4. **Invalidate related queries** after mutations
5. **Handle loading and error states** in components
6. **Use optimistic updates** when appropriate
7. **Implement proper error boundaries**

## Code Style

We prioritize **simple, readable code** over clever, short solutions. Code should be self-documenting and easy to understand.

### General Principles

1. **Clarity over Cleverness**: Write code that is easy to read and understand
2. **Explicit over Implicit**: Be explicit about intentions and dependencies
3. **Consistency**: Follow established patterns within the codebase
4. **Type Safety**: Leverage TypeScript for better developer experience

### Examples

#### ✅ Preferred: Simple and Clear

```typescript
// Clear variable names and explicit logic
const handleUserSubmission = async (formData: UserFormData) => {
  const isValidData = validateUserData(formData);
  if (!isValidData) {
    showErrorMessage("Please check your input");
    return;
  }

  try {
    const newUser = await createUser(formData);
    showSuccessMessage(`User ${newUser.name} created successfully`);
    redirectToUserList();
  } catch (error) {
    showErrorMessage("Failed to create user");
  }
};
```

#### ❌ Avoid: Overly Clever

```typescript
// Hard to read and debug
const handleUserSubmission = async (d: any) => 
  validateUserData(d) 
    ? createUser(d).then(u => (showSuccessMessage(`User ${u.name} created`), redirectToUserList())).catch(() => showErrorMessage("Failed"))
    : showErrorMessage("Invalid input");
```

### TypeScript Best Practices

1. **Use explicit types** for function parameters and return values
2. **Prefer types over interfaces** whenever possible
3. **Use generic constraints** when appropriate - limit generic types to specific shapes or capabilities
4. **Avoid `any`** - use `unknown` or proper types instead

#### Generic Constraints Examples

Use `extends` to constrain generic types to specific shapes:

```typescript
// ✅ Good: Constrain T to objects with an id property
function updateItem<T extends { id: string }>(item: T, updates: Partial<T>): T {
  return { ...item, ...updates };
}

// ✅ Good: Constrain to specific union types
function processStatus<T extends 'pending' | 'completed' | 'failed'>(status: T): string {
  return `Processing ${status} status`;
}

// ✅ Good: Constrain to keyof for safe property access
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// ❌ Avoid: Unconstrained generics can accept anything
function badUpdate<T>(item: T, updates: any): T {
  return { ...item, ...updates }; // No type safety
}
```

### Function Declaration Best Practices

**Prefer function declarations over function expressions and arrow functions** for named functions, especially at the top level:

```typescript
// ✅ Preferred: Function declarations
function validateUserData(data: UserData): boolean {
  return data.name && data.email;
}

function handleUserSubmission(formData: UserFormData): Promise<void> {
  // Implementation
}

// ✅ Good: Arrow functions for callbacks and short inline functions
const users = data.filter(user => user.isActive);

// ❌ Avoid: Function expressions for main functions
const validateUserData = function(data: UserData): boolean {
  return data.name && data.email;
};

// ❌ Avoid: Arrow functions for complex top-level functions
const handleUserSubmission = async (formData: UserFormData): Promise<void> => {
  // Complex implementation
};
```

**Benefits of function declarations:**
- **Hoisting**: Available throughout their scope
- **Better debugging**: Clear function names in stack traces
- **Cleaner syntax**: No need for const/let declarations
- **Consistent style**: Easier to read and maintain

### Component Best Practices

1. **Use descriptive component names**
2. **Keep components focused** on a single responsibility
3. **Extract reusable logic** into custom hooks
4. **Use proper prop types** with TypeScript types

## Validations

We use **[Zod](https://zod.dev/)** for all validation needs, including form validation.

### Key Dependencies

```json
{
  "zod": "^4.1.11"
}
```

### Validation Best Practices

1. **Validate at boundaries**: Forms, API responses, environment variables
2. **Use descriptive error messages**
3. **Create reusable schemas** for common patterns

### Custom Validation Schemas

```typescript
// lib/utils/validation.ts
import { z } from "zod";

export const kubernetesNameSchema = z.string()
  .min(1, "Name is required")
  .max(63, "Name must be less than 63 characters")
  .regex(/^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/, 
    "Name must contain only lowercase letters, numbers, and hyphens, and must start and end with an alphanumeric character");

export const emailSchema = z.string()
  .email("Invalid email address")
  .toLowerCase();

export const passwordSchema = z.string()
  .min(8, "Password must be at least 8 characters")
  .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
  .regex(/[a-z]/, "Password must contain at least one lowercase letter")
  .regex(/[0-9]/, "Password must contain at least one number");
```

## Examples

### Complete Form with API Integration

```tsx
"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCreateUser } from "@/lib/services/users-hooks";

const createUserSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Invalid email address"),
  role: z.enum(["admin", "user", "guest"], {
    required_error: "Please select a role",
  }),
});

type CreateUserFormData = z.infer<typeof createUserSchema>;

export function CreateUserForm() {
  const createUserMutation = useCreateUser();
  
  const form = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      name: "",
      email: "",
      role: undefined,
    },
  });

  const onSubmit = async (data: CreateUserFormData) => {
    try {
      await createUserMutation.mutateAsync(data);
      toast.success("User created successfully");
      form.reset();
    } catch (error) {
      toast.error("Failed to create user");
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="role"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Role</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a role" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="guest">Guest</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <Button 
          type="submit" 
          disabled={createUserMutation.isPending}
        >
          {createUserMutation.isPending ? "Creating..." : "Create User"}
        </Button>
      </form>
    </Form>
  );
}
```

### Data Fetching Component

```tsx
"use client";

import { useListUsers } from "@/lib/services/users-hooks";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription } from "@/components/ui/alert";

export function UsersList() {
  const { data: users, isPending, error } = useListUsers();

  if (isPending) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load users. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }

  if (!users || users.length === 0) {
    return (
      <div className="text-center text-muted-foreground p-8">
        No users found.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {users.map((user) => (
        <div key={user.id} className="border rounded-lg p-4">
          <h3 className="font-semibold">{user.name}</h3>
          <p className="text-muted-foreground">{user.email}</p>
        </div>
      ))}
    </div>
  );
}
```

This guide should serve as your reference for developing features in the Ark Dashboard. Remember to prioritize clarity, consistency, and type safety in all your code.