import React, { useState } from "react";
import { toast } from "sonner";
import { Image as ImageIcon, Trash2, Upload, Pencil, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TypoHeading, TypoSection, TypoCaption } from "@/components/shared/Typography";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";
import { organizationsApi } from "@/api/modules/organizations";

interface OrganizationBrandingProps {
  orgId: string;
  name: string;
  logoUrl?: string | null;
  bannerUrl?: string | null;
  onChange?: (updates: { logo_url?: string | null; banner_url?: string | null }) => void;
}

type BrandingField = "logo" | "banner";

interface ModalState {
  open: boolean;
  mode: "avatar" | "banner";
  initialImageUrl?: string;
  title: string;
}

export function OrganizationBranding({
  orgId,
  name,
  logoUrl,
  bannerUrl,
  onChange,
}: OrganizationBrandingProps) {
  const [modal, setModal] = useState<ModalState | null>(null);
  const [savingField, setSavingField] = useState<BrandingField | null>(null);

  const applyUpdate = (field: BrandingField, value: string | null) => {
    const updates = field === "logo" ? { logo_url: value } : { banner_url: value };
    onChange?.(updates);
  };

  const saveImage = async (field: BrandingField, value: string | null) => {
    setSavingField(field);
    try {
      const updated = await organizationsApi.update(orgId, {
        logo_url: field === "logo" ? value : undefined,
        banner_url: field === "banner" ? value : undefined,
      });
      applyUpdate(field, updated.logo_url ?? null);
      toast.success(field === "logo" ? "Organization logo updated" : "Organization cover updated");
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : `Failed to update ${field === "logo" ? "logo" : "cover"}.`;
      toast.error(msg);
    } finally {
      setSavingField(null);
    }
  };

  const handleUploadSuccess = (url: string) => {
    const field: BrandingField = modal?.mode === "avatar" ? "logo" : "banner";
    setModal(null);
    void saveImage(field, url);
  };

  const removeImage = (field: BrandingField) => {
    if (savingField) return;
    void saveImage(field, null);
  };

  const openModal = (field: BrandingField) => {
    if (field === "logo") {
      setModal({
        open: true,
        mode: "avatar",
        initialImageUrl: logoUrl ?? undefined,
        title: "Upload Organization Logo",
      });
    } else {
      setModal({
        open: true,
        mode: "banner",
        initialImageUrl: bannerUrl ?? undefined,
        title: bannerUrl ? "Reposition Organization Cover" : "Upload Organization Cover",
      });
    }
  };

  const isSaving = (field: BrandingField) => savingField === field;

  return (
    <div className="space-y-8">
      <div>
        <TypoHeading as="h2">Branding</TypoHeading>
        <TypoCaption as="p">
          Upload and customize your organization logo and cover image. Changes are saved immediately
          and visible to everyone on your public profile.
        </TypoCaption>
      </div>

      {/* Live Preview */}
      <div>
        <TypoSection className="mb-2">Preview</TypoSection>
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden">
          <div className="h-28 sm:h-36 w-full bg-gradient-to-r from-blue-900 to-indigo-900 relative">
            {bannerUrl && (
              <img src={bannerUrl} alt={`${name} cover`} className="w-full h-full object-cover" />
            )}
          </div>
          <div className="p-4 sm:p-6 -mt-8 sm:-mt-10 relative flex items-end gap-3">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl border-4 border-gray-900 bg-gray-800 overflow-hidden flex items-center justify-center font-bold text-xl text-white shadow-lg">
              {logoUrl ? (
                <img src={logoUrl} alt={`${name} logo`} className="w-full h-full object-cover" />
              ) : (
                name.slice(0, 2).toUpperCase()
              )}
            </div>
            <div>
              <p className="text-lg font-semibold text-white">{name}</p>
              <p className="text-xs text-gray-400">Live preview · shown on your profile</p>
            </div>
          </div>
        </div>
      </div>

      {/* Logo */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/30 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-400 shrink-0">
              {logoUrl ? (
                <img
                  src={logoUrl}
                  alt={`${name} logo`}
                  className="w-full h-full object-cover rounded-xl"
                />
              ) : (
                <ImageIcon size={22} />
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-white">Organization Logo</p>
              <TypoCaption as="p">
                Square image shown next to your organization name. Recommended 1:1 ratio.
              </TypoCaption>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => openModal("logo")}
              disabled={isSaving("logo")}
              className="gap-2"
            >
              <Upload size={14} />
              {logoUrl ? "Replace Logo" : "Upload Logo"}
            </Button>
            {logoUrl && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => removeImage("logo")}
                disabled={isSaving("logo")}
                className="gap-2 text-destructive hover:text-destructive"
              >
                {isSaving("logo") ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Trash2 size={14} />
                )}
                Remove
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Cover */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/30 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-400 shrink-0 overflow-hidden">
              {bannerUrl ? (
                <img src={bannerUrl} alt={`${name} cover`} className="w-full h-full object-cover" />
              ) : (
                <ImageIcon size={22} />
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-white">Cover Image</p>
              <TypoCaption as="p">
                Wide banner shown at the top of your profile. Recommended 3:1 ratio.
              </TypoCaption>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => openModal("banner")}
              disabled={isSaving("banner")}
              className="gap-2"
            >
              {bannerUrl ? (
                <>
                  <Pencil size={14} />
                  Reposition Cover
                </>
              ) : (
                <>
                  <Upload size={14} />
                  Upload Cover
                </>
              )}
            </Button>
            {bannerUrl && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => removeImage("banner")}
                disabled={isSaving("banner")}
                className="gap-2 text-destructive hover:text-destructive"
              >
                {isSaving("banner") ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Trash2 size={14} />
                )}
                Remove
              </Button>
            )}
          </div>
        </div>
      </div>

      {modal && (
        <ImageCropUploadModal
          isOpen={modal.open}
          onClose={() => setModal(null)}
          onUploadSuccess={handleUploadSuccess}
          mode={modal.mode}
          title={modal.title}
          initialImageUrl={modal.initialImageUrl}
        />
      )}
    </div>
  );
}
