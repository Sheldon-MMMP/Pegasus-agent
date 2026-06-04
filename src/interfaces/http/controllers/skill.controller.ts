import type { Request, Response } from "express";
import * as skillService from "../../../services/skill.service.js";
import { uuidSchema } from "../schemas/common.schema.js";
import { createSkillSchema, updateSkillSchema } from "../schemas/skill.schema.js";

export async function listSkills(_request: Request, response: Response): Promise<void> {
  response.json(await skillService.listSkills());
}

export async function getSkill(request: Request, response: Response): Promise<void> {
  response.json(await skillService.getSkill(uuidSchema.parse(request.params.skillId)));
}

export async function createSkill(request: Request, response: Response): Promise<void> {
  response.json(await skillService.createSkill(createSkillSchema.parse(request.body)));
}

export async function updateSkill(request: Request, response: Response): Promise<void> {
  response.json(
    await skillService.updateSkill(
      uuidSchema.parse(request.params.skillId),
      updateSkillSchema.parse(request.body),
    ),
  );
}
