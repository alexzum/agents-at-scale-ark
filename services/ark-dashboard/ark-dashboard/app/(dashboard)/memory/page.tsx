import { MemorySection } from "@/components/sections"
import { BreadcrumbElement, PageHeader } from "@/components/common/page-header"

const breadcrumbs: BreadcrumbElement[] = [
  { href: '/', label: "ARK Dashboard" }
]

export default function MemoryPage() {
  return (
    <>
      <PageHeader breadcrumbs={breadcrumbs} currentPage="Memory" />
      <div className="flex flex-1 flex-col">
        <MemorySection />
      </div>
    </>
  )
}