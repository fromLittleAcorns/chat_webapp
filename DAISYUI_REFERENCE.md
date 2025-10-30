# DaisyUI Components Reference

Quick reference for the DaisyUI components used in this application.

## Chat Components

### Chat Container
```python
Div(cls="chat chat-start")  # Assistant messages (left aligned)
Div(cls="chat chat-end")    # User messages (right aligned)
```

### Chat Bubble
```python
Div(cls="chat-bubble chat-bubble-primary")    # User bubble (primary color)
Div(cls="chat-bubble chat-bubble-secondary")  # Assistant bubble (secondary color)
```

### Chat Header/Footer
```python
Div(cls="chat-header")  # Above bubble (role label)
Div(cls="chat-footer")  # Below bubble (timestamp)
```

## Layout Components

### Drawer (Sidebar)
```python
Div(cls="drawer lg:drawer-open")  # Main container, drawer always open on large screens
Div(cls="drawer-side")             # Sidebar content
Div(cls="drawer-content")          # Main content area
```

### Menu
```python
Ul(cls="menu")                     # Menu container
Li(cls="active")                   # Active menu item
```

## Form Components

### Input
```python
Textarea(cls="textarea textarea-bordered")  # Text area with border
Input(cls="input input-bordered")           # Input with border
```

### Button
```python
Button(cls="btn btn-primary")      # Primary button
Button(cls="btn btn-ghost")        # Ghost button (transparent)
Button(cls="btn btn-outline")      # Outline button
Button(cls="btn btn-sm")           # Small button
Button(cls="btn btn-xs")           # Extra small button
Button(cls="btn-square")           # Square button (icon only)
```

## Feedback Components

### Alert
```python
Div(cls="alert alert-error")       # Error alert (red)
Div(cls="alert alert-warning")     # Warning alert (yellow)
Div(cls="alert alert-info")        # Info alert (blue)
Div(cls="alert alert-success")     # Success alert (green)
```

### Loading
```python
Span(cls="loading loading-spinner")         # Spinner
Span(cls="loading loading-dots")            # Dots
Span(cls="loading loading-spinner loading-lg")  # Large spinner
Span(cls="loading loading-dots loading-sm")     # Small dots
```

## Content Components

### Hero
```python
Div(cls="hero")                    # Hero container
Div(cls="hero-content")            # Hero content wrapper
```

## Utility Classes

### Spacing
```python
cls="p-4"    # Padding all sides (1rem)
cls="px-4"   # Padding left/right
cls="py-4"   # Padding top/bottom
cls="m-4"    # Margin all sides
cls="mt-4"   # Margin top
cls="gap-2"  # Gap between flex/grid items
```

### Sizing
```python
cls="w-full"        # Width 100%
cls="w-80"          # Width 20rem
cls="h-full"        # Height 100%
cls="min-h-[60vh]"  # Min height 60% viewport
```

### Flexbox
```python
cls="flex"              # Display flex
cls="flex-col"          # Flex direction column
cls="items-center"      # Align items center
cls="justify-between"   # Space between items
cls="gap-4"             # Gap between items
```

### Typography
```python
cls="text-xl"           # Extra large text
cls="text-3xl"          # 3x large text
cls="font-bold"         # Bold text
cls="font-semibold"     # Semi-bold text
cls="opacity-50"        # 50% opacity
cls="text-center"       # Center align text
```

### Colors
```python
cls="text-error"        # Error color text
cls="text-primary"      # Primary color text
cls="bg-base-200"       # Base background color
cls="bg-base-100"       # Lighter base background
```

### Layout
```python
cls="fixed"             # Fixed positioning
cls="absolute"          # Absolute positioning
cls="relative"          # Relative positioning
cls="z-10"              # Z-index 10
```

### Borders
```python
cls="border"            # Border all sides
cls="border-t"          # Border top
cls="rounded-lg"        # Large border radius
```

## Responsive Modifiers

```python
cls="lg:drawer-open"    # Apply on large screens and up
cls="lg:left-80"        # Left 20rem on large screens
```

Breakpoints:
- `sm:` - 640px
- `md:` - 768px
- `lg:` - 1024px
- `xl:` - 1280px
- `2xl:` - 1536px

## Color Theme Variables

DaisyUI uses CSS variables for theming:
```css
hsl(var(--p))      /* Primary color */
hsl(var(--s))      /* Secondary color */
hsl(var(--a))      /* Accent color */
hsl(var(--n))      /* Neutral color */
hsl(var(--b1))     /* Base-100 */
hsl(var(--b2))     /* Base-200 */
hsl(var(--b3))     /* Base-300 */
```

## Documentation Links

- DaisyUI Components: https://daisyui.com/components/
- Tailwind Utilities: https://tailwindcss.com/docs/utility-first
- Chat Component: https://daisyui.com/components/chat/
- Drawer Component: https://daisyui.com/components/drawer/
- Menu Component: https://daisyui.com/components/menu/
