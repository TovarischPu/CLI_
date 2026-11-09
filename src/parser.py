import xml.etree.ElementTree as et

MAVEN_NS = "http://maven.apache.org/POM/4.0.0"
NS_MAP = {"m": MAVEN_NS}


def build_pom_url(source: str, package: str) -> str:
    parts = package.split(":")
    if len(parts) == 3:
        group, artifact, version = parts
    elif len(parts) == 2:
        group, artifact = parts
        version = "RELEASE"
    else:
        raise ValueError(f"Неверный формат пакета: {package}")

    group_path = group.replace(".", "/")
    return (
        f"{source.rstrip('/')}/{group_path}/{artifact}/"
        f"{version}/{artifact}-{version}.pom"
    )


def parse_direct_dependencies(xml_text: str) -> list[dict]:
    root = et.fromstring(xml_text)
    dependencies = []
    deps_block = root.find("m:dependencies", NS_MAP)
    if deps_block is None:
        deps_block = root.find("dependencies")
        
    if deps_block is not None:
        dep_elements = deps_block.findall("m:dependency", NS_MAP)
        if not dep_elements:
            dep_elements = deps_block.findall("dependency")
            
        for dep in dep_elements:
            group = dep.find("m:groupId", NS_MAP)
            if group is None:
                group = dep.find("groupId")
                
            artifact = dep.find("m:artifactId", NS_MAP)
            if artifact is None:
                artifact = dep.find("artifactId")
                
            version = dep.find("m:version", NS_MAP)
            if version is None:
                version = dep.find("version")
            
            if group is not None and artifact is not None:
                ver_text = version.text if version is not None else "RELEASE"
                dependencies.append({
                    "groupId": group.text,
                    "artifactId": artifact.text,
                    "version": ver_text,
                })
                
    return dependencies