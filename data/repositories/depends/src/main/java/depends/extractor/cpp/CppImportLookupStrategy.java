/*
MIT License

Copyright (c) 2018-2019 Gang ZHANG

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

package depends.extractor.cpp;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.List;

import depends.entity.Entity;
import depends.entity.FileEntity;
import depends.entity.repo.EntityRepo;
import depends.importtypes.FileImport;
import depends.importtypes.Import;
import depends.relations.ImportLookupStrategy;
import depends.relations.Inferer;

public class CppImportLookupStrategy implements ImportLookupStrategy {
	@Override
	public Entity lookupImportedType(String name, FileEntity fileEntity, EntityRepo repo, Inferer inferer) {
		String importedString = fileEntity.importedSuffixMatch(name);
		if (importedString!=null) {
			Entity r = repo.getEntity(importedString);
			if (r!=null) return r;
		}
		
		HashSet<String> fileSet = new HashSet<>();
		foundIncludedFiles(fileSet, fileEntity.getImportedFiles(),repo);
		
		for (String file:fileSet) {
			Entity importedItem = repo.getEntity(file);
			if (importedItem instanceof FileEntity) {
				FileEntity importedFile = (FileEntity) repo.getEntity(file);
				if (importedFile==null) continue;
				 Entity entity = inferer.resolveName(importedFile,name, false);
				if (entity!=null) return entity;
				Collection<Entity> namespaces = fileEntity.getImportedTypes();
				for (Entity ns:namespaces) {
					String nameWithPrefix = ns.getQualifiedName() + "." + name;
					entity = inferer.resolveName(importedFile,nameWithPrefix, false);
					if (entity!=null) return entity;				
				}
			}	
		}		
		return null;
	}

	private void foundIncludedFiles(HashSet<String> fileSet, Collection<Entity> importedFiles, EntityRepo repo) {
		for (Entity file:importedFiles) {
			if (file==null ) continue;
			if (!(file instanceof FileEntity)) continue;
			if (fileSet.contains(file.getRawName())) continue;
			fileSet.add(file.getRawName());
			foundIncludedFiles(fileSet,((FileEntity)file).getImportedFiles(),repo);
		}
	}
	
	
	@Override
	public List<Entity> getImportedRelationEntities(List<Import> importedList, EntityRepo repo) {
		ArrayList<Entity> result = new ArrayList<>();
		for (Import importedItem:importedList) {
			if (importedItem instanceof FileImport) {
				Entity imported = repo.getEntity(importedItem.getContent());
				if (imported==null) continue;
				result.add(imported);
			}
		}
		return result;
	}

	@Override
	public List<Entity> getImportedTypes(List<Import> importedList, EntityRepo repo) {
		ArrayList<Entity> result = new ArrayList<>();
		for (Import importedItem:importedList) {
			if (!(importedItem instanceof FileImport)) {
				Entity imported = repo.getEntity(importedItem.getContent());
				if (imported==null) continue;
				result.add(imported);
			}
		}
		return result;
	}

	@Override
	public List<Entity> getImportedFiles(List<Import> importedList, EntityRepo repo) {
		return getImportedRelationEntities(importedList,repo);
	}
	
	@Override
	public boolean supportGlobalNameLookup() {
		return false;
	}
}
