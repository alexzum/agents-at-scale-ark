import { ComponentProps, Fragment, ReactNode } from "react"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbLink,
  BreadcrumbEllipsis,
  BreadcrumbSeparator
} from "@/components/ui/breadcrumb"

import Link from "next/link"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu"
import { Tooltip, TooltipContent, TooltipTrigger } from "../ui/tooltip"
import { Button } from "../ui/button"
import { Info } from "lucide-react"

export type BreadcrumbElement = {
  label: string;
  href: ComponentProps<typeof Link>["href"];
}

type BreadcrumbsDropdownProps = {
  elements: BreadcrumbElement[]
}

function BreadcrumbsDropdown({ elements }: BreadcrumbsDropdownProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-1">
        <BreadcrumbEllipsis className="size-4" />
        <span className="sr-only">Toggle menu</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        {elements.map((e) => (
          <Link href={e.href} key={e.label}>
            <DropdownMenuItem >{e.label}</DropdownMenuItem>
          </Link>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

type BreadcrumbsLinksProps = {
  elements?: BreadcrumbElement[]
}

function BreadcrumbsLinks({ elements }: BreadcrumbsLinksProps) {
  return (
    <>
      {elements?.map((link) => (
        <Fragment key={link.label}>
          <BreadcrumbItem >
            <BreadcrumbLink asChild>
              <Link href={link.href}>{link.label}</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
        </Fragment>
      ))
      }
    </>
  )
}

function HeaderTooltip() {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Link href="https://mckinsey.github.io/agents-at-scale-ark/">
          <Button variant="ghost">
            <Info className="h-4 w-4" />
          </Button>
        </Link>
      </TooltipTrigger>
      <TooltipContent>
        <span>Help</span>
      </TooltipContent>
    </Tooltip>
  )
}

type PageHeaderProps = {
  breadcrumbs?: BreadcrumbElement[]
  currentPage: string
  actions?: ReactNode
}

export function PageHeader({ breadcrumbs, currentPage, actions }: PageHeaderProps) {
  const firstCrumb = (breadcrumbs?.length || 0) > 2 ? breadcrumbs?.[0] : undefined;
  const crumbsInDropdown = (breadcrumbs?.length || 0) > 2 ? breadcrumbs?.slice(1, -1) : undefined;
  const visibleCrumbs = (breadcrumbs?.length || 0) > 2 ? breadcrumbs?.slice(-1) : breadcrumbs;

  return (
    <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
      {/* Mobile */}
      <Breadcrumb className="block md:hidden">
        <BreadcrumbList>
          {breadcrumbs?.length ? (
            <>
              <BreadcrumbItem>
                <BreadcrumbsDropdown elements={breadcrumbs} />
              </BreadcrumbItem>
              <BreadcrumbSeparator />
            </>
          ) : null}
          <BreadcrumbItem>
            <BreadcrumbPage>{currentPage}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      {/* Desktop */}
      <Breadcrumb className="hidden md:block">
        <BreadcrumbList>
          {firstCrumb && (
            <>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link href={firstCrumb.href}>
                    {firstCrumb.label}
                  </Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
            </>
          )}
          {crumbsInDropdown ? (
            <>
              <BreadcrumbItem>
                <BreadcrumbsDropdown elements={crumbsInDropdown} />
              </BreadcrumbItem>
              <BreadcrumbSeparator />
            </>
          ) : null}
          <BreadcrumbsLinks elements={visibleCrumbs} />
          <BreadcrumbItem>
            <BreadcrumbPage>{currentPage}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="ml-auto space-x-2 flex items-center">
        {actions && (actions)}
        <HeaderTooltip />
      </div>
    </header>
  )
}
