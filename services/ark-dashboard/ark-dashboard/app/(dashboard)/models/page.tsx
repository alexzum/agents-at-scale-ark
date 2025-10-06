"use client"

import { ModelsSection } from "@/components/sections/models-section"
import { useSearchParams } from "next/navigation"
import { Suspense } from "react"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import Link from "next/link"

function ModelsContent() {
  const searchParams = useSearchParams()
  const namespace = searchParams.get("namespace") || "default"

  return (
    <>
      <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage>Models</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <div className="ml-auto">
          <Link href="/models/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Model
            </Button>
          </Link>
        </div>
      </header>
      <div className="flex flex-1 flex-col">
        <ModelsSection namespace={namespace} />
      </div>
    </>
  )
}

export default function ModelsPage() {
  return (
    <Suspense fallback={<div className="flex h-full items-center justify-center">Loading...</div>}>
      <ModelsContent />
    </Suspense>
  )
}