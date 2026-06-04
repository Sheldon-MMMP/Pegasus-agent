import type { Request, Response } from "express";
import * as settingsService from "../../../services/settings.service.js";
import { updateSettingsSchema } from "../schemas/settings.schema.js";

export async function getSettings(_request: Request, response: Response): Promise<void> {
  response.json(await settingsService.getSettings());
}

export async function updateSettings(request: Request, response: Response): Promise<void> {
  response.json(await settingsService.updateSettings(updateSettingsSchema.parse(request.body)));
}
