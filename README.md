# EBUCorePlus

<p >
The <a href="https://www.ebu.ch/metadata/ontologies/ebucoreplus/index.html"> EBUCorePlus </a> is an ontology for media enterprises, developed as an open source project. It follows-up on two long-standing EBU ontologies: EBUCore and CCDM (Class Conceptual Data Model). The two were merged and thoroughly revisioned. The result is EBUCorePlus, the new standard that can fully replace its predecessors. It inherits both the long-lasting reliability of EBUCore and the end-to-end coverage of the media value chain of CCDM. 
</p>
<p >
EBUCorePlus is strictly semantic. It avoids ambiguities that were introduced when using EBUCore and CCDM classes in one graph. It has its own, new name space therefore it is not backward compatible, but can be mapped to its predecessors. It provides complete documentation of all entities in English, French and German (English being normative).
</p>

<p align="center" >
<img width="1440" alt="EBUCorePlus-Overview-1-0-2-transparent" src="https://user-images.githubusercontent.com/32091198/235692418-6cd35145-4f7f-4727-805b-f1ec2ded40ef.png">
<em>Overview of the EBUCorePlus</em>  
</p>

</p>
One major problem of EBUCore and CCDM was the use of ranges: semantically similar object properties needed to be defined in parallel for each class that the property referred to. Another case was the use of multi-range properties, leading to insufficient type safety. EBUCorePlus now uses class restrictions instead, leading to less and more coherent properties. 
</p>
<p >
EBUCorePlus aims to serve as a plug and play framework. It can be used out of the box, either in its entirety or just a subset of its elements. But it may also be adapted and extended to enterprise-specific needs. It is not required to adopt the ontology completely. The benefit from using EBUCorePlus arises from combining well-defined modelling proposals with your use case specific decisions. Especially for system integration tasks and defining requirements, projects benefit from EBUCorePlus as a business – not technology – oriented language. 
</p>
<p >
The ontology is developed by the EBU Metadata Modelling Working Group as an open source project on github. Requests for changes and improvements can be submitted by EBU Members, media organizations or anybody else from the media community. The EBUCorePlus Editorial Committee reviews requests and implements changes. 
</p>
<p >
The <a href="https://tech.ebu.ch/groups/mm"> EBU Metadata Modelling Working Group </a> provides access, <a href="mailto:rouxel@ebu.ch"> upon request </a> to a cloud hosted demonstration kit to explore and better understand the whole EBUCorePlus model.
</p>

# How we use annotation properties for definition, examples and description

## Starting with **dcterms:description**
The preceding ontologies EBUCore and CCDM annotated their entities with the property **dcterms:description**. The Literals were filled with descriptive text, mostly explaining, what the entity’s purpose was:
```
ec:isBrand dcterms:description “To identify a Brand.”@en
```
Or the Literals referenced the term itself to be described:
```
ec:Person dcterms:description "A Person."@en
```

## Applying guidelines
While the **dcterms:descriptions** are useful in many circumstances, they seemed insufficient to us. We wanted to achieve the best possible precision and common understanding for EBUCorePlus entities. So, we applied the <a href="https://philpapers.org/archive/SEPGFW.pdf"> “Guidelines for writing definition in ontologies”  </a> , a great paper by Seppälä, Ruttenberg and Smith.

## Using skos:definition and skos:examples
SKOS provides the annotation properties **skos:definition** and **skos:example** that match our intended use perfectly. The Literals in these annotations are created according to the guidelines of the paper. E.g.
```
ec:Person skos:definition = “an individual Agent”@en
```
In this case it is stated that “Person” is a specific “Agent” representing an indivisible human being.

The Literals in **skos:example** list representatives that are most common, but sometimes also most rare, in order to enlighten the borders of the defintion’s scope:
```
ec:Person skos:example """- Alfred Hitchcock (director)
                          - James Bond (character)
                          - Sean Connery (actor)
                          - John Ford (pseudonym used by the director John Martin Feeney)"""
```
## Examining annotations
We consider **skos:definition** to provide the normative text for defintions and **skos:example** as a way to simplify understanding of the definitions, because sometimes the definitions are very formal. However, we have not yet equipped all entities with **skos:definitions** yet and we understand that **dcterms:descriptions** are covering almost all entities and therefore are still helpful, even if they might be unprecise, outdated or even wrong (e.g because the meaning of an entity has changed from EBUCore to EBUCorePlus). So, when examining the annotations, be aware that **skos:definition** is normative but may be lacking and **dcterms:description** is complete but to be interpreted carefully.

## Translations to French and German
EBUCorePlus aims to provide full documentation in 3 languages: English, French and German. We hope to lower the barriers for non-native English speakers. To accomplish this in due time, we made heavy use of automatic translations from English to French and German. Be aware, that automatic translation is varying in quality. But so are many English texts in EBUCore and CCDM, because they were created by non-native speakers. The EBU working group is editing and improving the Literals in EBUCorePlus step by step.

